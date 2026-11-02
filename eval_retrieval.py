import argparse
import json
from pathlib import Path

from ask import retrieve
from config import BASE_DIR, RERANK_POOL, TOP_K
from rerank import rerank

GOLDEN_PATH = BASE_DIR / "data" / "golden.jsonl"


def load_golden(path: Path) -> list[dict]:
    items = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def is_hit(chunk: dict, item: dict) -> bool:
    if chunk["source"] != item["source"]:
        return False
    evidence = item.get("evidence", "").strip().lower()
    return not evidence or evidence in chunk["text"].lower()


def first_hit_rank(chunks: list[dict], item: dict) -> int | None:
    for rank, chunk in enumerate(chunks, start=1):
        if is_hit(chunk, item):
            return rank
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=TOP_K)
    parser.add_argument("--golden", type=Path, default=GOLDEN_PATH)
    parser.add_argument("--rerank", action="store_true")
    parser.add_argument("--pool", type=int, default=RERANK_POOL)
    args = parser.parse_args()

    items = [i for i in load_golden(args.golden) if i.get("answerable", True)]
    if not items:
        raise SystemExit("No answerable questions in golden set")

    hits = 0
    reciprocal_ranks = []
    for item in items:
        if args.rerank:
            pool = retrieve(item["question"], top_k=args.pool)
            chunks = rerank(item["question"], pool, args.k)
        else:
            chunks = retrieve(item["question"], top_k=args.k)
        rank = first_hit_rank(chunks, item)
        if rank is None:
            reciprocal_ranks.append(0.0)
            print(f"MISS [{item['id']}] {item['question']}")
            print("  got:", [(c["source"], c["chunk"]) for c in chunks])
        else:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)

    n = len(items)
    mode = f"rerank pool={args.pool}" if args.rerank else "no rerank"
    print(f"\nQuestions: {n}, k={args.k}, {mode}")
    print(f"Hit rate@{args.k}: {hits / n:.3f}")
    print(f"MRR@{args.k}: {sum(reciprocal_ranks) / n:.3f}")


if __name__ == "__main__":
    main()
