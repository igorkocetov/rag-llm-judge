import sys

import chromadb
import ollama

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBED_MODEL,
    GEN_MODEL,
    RERANK_POOL,
    TOP_K,
    USE_RERANK,
)
from rerank import rerank

PROMPT = """Ответь на вопрос, используя только контекст ниже.
Если в контексте нет ответа, скажи: "В документах нет ответа на этот вопрос".

Контекст:
{context}

Вопрос: {question}
"""


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    query_emb = ollama.embed(model=EMBED_MODEL, input=question)["embeddings"]
    result = collection.query(query_embeddings=query_emb, n_results=top_k)
    return [
        {"text": doc, "source": meta["source"], "chunk": meta["chunk"]}
        for doc, meta in zip(result["documents"][0], result["metadatas"][0])
    ]


def search(question: str, top_k: int = TOP_K) -> list[dict]:
    if USE_RERANK:
        return rerank(question, retrieve(question, top_k=RERANK_POOL), top_k)
    return retrieve(question, top_k=top_k)


def answer(question: str) -> tuple[str, list[dict]]:
    chunks = search(question)
    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    response = ollama.chat(
        model=GEN_MODEL,
        messages=[
            {"role": "user", "content": PROMPT.format(context=context, question=question)}
        ],
    )
    return response["message"]["content"], chunks


def main() -> None:
    question = " ".join(sys.argv[1:]) or input("Вопрос: ")
    text, chunks = answer(question)
    print("\nОтвет:\n", text)
    print("\nИсточники:")
    for c in chunks:
        print(f"- {c['source']} (chunk {c['chunk']})")


if __name__ == "__main__":
    main()
