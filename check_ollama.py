import ollama

from config import EMBED_MODEL, GEN_MODEL


def main() -> None:
    print(f"Generation model: {GEN_MODEL}")
    response = ollama.chat(
        model=GEN_MODEL,
        messages=[{"role": "user", "content": "Ответь одним словом: столица России?"}],
    )
    print("Answer:", response["message"]["content"])

    print(f"Embedding model: {EMBED_MODEL}")
    emb = ollama.embed(model=EMBED_MODEL, input="проверка эмбеддингов")
    print("Embedding dim:", len(emb["embeddings"][0]))


if __name__ == "__main__":
    main()
