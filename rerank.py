from sentence_transformers import CrossEncoder

from config import RERANK_MODEL

_model: CrossEncoder | None = None


def rerank(question: str, chunks: list[dict], top_k: int) -> list[dict]:
    global _model
    if _model is None:
        _model = CrossEncoder(RERANK_MODEL)
    scores = _model.predict([(question, c["text"]) for c in chunks])
    ranked = sorted(zip(scores, chunks), key=lambda pair: pair[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]
