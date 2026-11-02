import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "data" / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "docs"

GEN_MODEL = os.getenv("GEN_MODEL", "qwen3:4b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "qwen3.5:9b")

GOLDEN_PATH = BASE_DIR / "data" / "golden.jsonl"
ANSWERS_PATH = BASE_DIR / "data" / "answers.jsonl"
JUDGMENTS_PATH = BASE_DIR / "data" / "judgments.jsonl"

CHUNK_MODE = os.getenv("CHUNK_MODE", "fixed")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K = int(os.getenv("TOP_K", "4"))

RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
RERANK_POOL = int(os.getenv("RERANK_POOL", "30"))
USE_RERANK = os.getenv("RERANK", "0") == "1"
