import re

import chromadb
import ollama

from config import (
    CHROMA_DIR,
    CHUNK_MODE,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DOCS_DIR,
    EMBED_MODEL,
)


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    chunks = []
    step = max(size - overlap, 1)
    for start in range(0, len(text), step):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append(piece)
    return chunks


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def split_by_headings(text: str) -> list[tuple[list[str], str]]:
    sections = []
    stack: list[tuple[int, str]] = []
    current: list[str] = []
    current_path: list[str] = []
    in_code = False

    def flush() -> None:
        body = "\n".join(current).strip()
        if body:
            sections.append((current_path, body))

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        match = None if in_code else HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).replace("**", "").strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current = [line]
            current_path = [t for _, t in stack]
        else:
            current.append(line)
    flush()
    return sections


def chunk_by_headings(text: str, file_name: str, size: int, overlap: int) -> list[str]:
    chunks = []
    for heading_path, body in split_by_headings(text):
        prefix = f"Файл: {file_name}\n"
        if heading_path:
            prefix += f"Раздел: {' > '.join(heading_path)}\n"
        for piece in chunk_text(body, size, overlap):
            chunks.append(f"{prefix}\n{piece}")
    return chunks


def make_chunks(text: str, file_name: str) -> list[str]:
    if CHUNK_MODE == "heading":
        return chunk_by_headings(text, file_name, CHUNK_SIZE, CHUNK_OVERLAP)
    return chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)


def main() -> None:
    print(f"Chunk mode: {CHUNK_MODE}, size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    files = sorted(DOCS_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files found in {DOCS_DIR}")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    for path in files:
        text = path.read_text(encoding="utf-8")
        chunks = make_chunks(text, path.name)
        if not chunks:
            continue
        embeddings = ollama.embed(model=EMBED_MODEL, input=chunks)["embeddings"]
        collection.add(
            ids=[f"{path.name}:{i}" for i in range(len(chunks))],
            documents=chunks,
            embeddings=embeddings,
            metadatas=[{"source": path.name, "chunk": i} for i in range(len(chunks))],
        )
        print(f"{path.name}: {len(chunks)} chunks")

    print("Total chunks:", collection.count())


if __name__ == "__main__":
    main()
