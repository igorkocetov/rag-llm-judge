import argparse
import json
from pathlib import Path

import ollama

from ask import answer
from config import (
    ANSWERS_PATH,
    GEN_MODEL,
    GOLDEN_PATH,
    JUDGE_MODEL,
    JUDGMENTS_PATH,
)

JUDGE_PROMPT = """Ты строгий эксперт-оценщик ответов RAG-системы.
Оцени ОТВЕТ СИСТЕМЫ на вопрос, сравнив с ЭТАЛОНОМ и КОНТЕКСТОМ.

Критерии (целые числа от 1 до 5). Оценивай каждый критерий НЕЗАВИСИМО от остальных.

- correctness: соответствует ли ответ эталону по смыслу.
  5 - полностью; 3-4 - верно, но неполно или неточно; 1-2 - неверно, противоречит эталону или ложный отказ.
  Форма ответа (например, повтор вопроса в начале) на оценку не влияет.

- groundedness: подтверждены ли КОНТЕКСТОМ те утверждения, которые ответ ДЕЙСТВИТЕЛЬНО делает.
  Проверяй только сказанное в ответе. То, что в ответе чего-то не хватает, на эту оценку НЕ влияет (это относится к completeness).
  Оценку 5 ставь, если все сделанные утверждения прямо есть в КОНТЕКСТЕ.
  Оценку 1 ставь, только если в ответе есть утверждения, которых нет в КОНТЕКСТЕ или которые ему противоречат.
  Не используй свои знания и эталон для проверки groundedness, только КОНТЕКСТ.
  Если ответ - отказ вида "в документах нет ответа": ставь 5, если КОНТЕКСТ действительно не содержит ответа на вопрос; ставь 1, если ответ в КОНТЕКСТЕ есть.

- completeness: какая доля ключевых пунктов эталона названа в ответе.
  Посчитай пункты эталона и сколько из них есть в ответе. Все пункты - 5; не хватает одного небольшого пункта - 4; около половины - 3; один-два пункта из многих - 2; почти ничего или отказ при наличии ответа - 1.

{unanswerable_note}
Вопрос: {question}

ЭТАЛОН: {reference}

КОНТЕКСТ:
{context}

ОТВЕТ СИСТЕМЫ: {model_answer}

В поле reason кратко укажи, какие утверждения ответа есть в КОНТЕКСТЕ и какие пункты эталона не названы.
Верни только JSON с полями correctness, groundedness, completeness, reason (одно короткое предложение)."""

UNANSWERABLE_NOTE = (
    "В документах ответа на этот вопрос НЕТ. Правильное поведение системы - "
    "честно сказать, что в документах нет ответа. Если система так и ответила, "
    "ставь correctness=5, groundedness=5, completeness=5. Если система выдумала "
    "ответ, ставь correctness=1 и groundedness=1.\n"
)

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "correctness": {"type": "integer", "minimum": 1, "maximum": 5},
        "groundedness": {"type": "integer", "minimum": 1, "maximum": 5},
        "completeness": {"type": "integer", "minimum": 1, "maximum": 5},
        "reason": {"type": "string"},
    },
    "required": ["correctness", "groundedness", "completeness", "reason"],
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def chat_json(model: str, prompt: str) -> dict:
    kwargs = dict(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=JUDGE_SCHEMA,
        options={"temperature": 0},
    )
    try:
        response = ollama.chat(think=False, **kwargs)
    except TypeError:
        response = ollama.chat(**kwargs)
    return json.loads(response["message"]["content"])


def generate_answers() -> None:
    golden = read_jsonl(GOLDEN_PATH)
    done = {row["id"] for row in read_jsonl(ANSWERS_PATH)}
    todo = [item for item in golden if item["id"] not in done]
    print(f"Generation model: {GEN_MODEL}. To do: {len(todo)} of {len(golden)}")
    for item in todo:
        text, chunks = answer(item["question"])
        append_jsonl(
            ANSWERS_PATH,
            {
                "id": item["id"],
                "question": item["question"],
                "answer": text,
                "chunks": [
                    {"source": c["source"], "chunk": c["chunk"], "text": c["text"]}
                    for c in chunks
                ],
            },
        )
        print(f"[{item['id']}] done")


def judge_answers() -> None:
    golden = {item["id"]: item for item in read_jsonl(GOLDEN_PATH)}
    answers = read_jsonl(ANSWERS_PATH)
    done = {row["id"] for row in read_jsonl(JUDGMENTS_PATH)}
    todo = [a for a in answers if a["id"] not in done]
    print(f"Judge model: {JUDGE_MODEL}. To do: {len(todo)} of {len(answers)}")
    for row in todo:
        item = golden[row["id"]]
        answerable = item.get("answerable", True)
        reference = item["reference_answer"] if answerable else "В документах нет ответа на этот вопрос"
        context = "\n\n---\n\n".join(c["text"] for c in row["chunks"])
        prompt = JUDGE_PROMPT.format(
            unanswerable_note="" if answerable else UNANSWERABLE_NOTE,
            question=row["question"],
            reference=reference,
            context=context,
            model_answer=row["answer"],
        )
        try:
            scores = chat_json(JUDGE_MODEL, prompt)
        except Exception as exc:
            print(f"[{row['id']}] judge failed: {exc}")
            continue
        append_jsonl(
            JUDGMENTS_PATH,
            {"id": row["id"], "answerable": answerable, **scores},
        )
        print(
            f"[{row['id']}] c={scores['correctness']} "
            f"g={scores['groundedness']} f={scores['completeness']}"
        )


def summary() -> None:
    rows = read_jsonl(JUDGMENTS_PATH)
    if not rows:
        raise SystemExit("No judgments yet")
    for label, flag in (("answerable", True), ("unanswerable", False)):
        part = [r for r in rows if r["answerable"] == flag]
        if not part:
            continue
        n = len(part)
        print(f"\n{label}: {n} questions")
        for key in ("correctness", "groundedness", "completeness"):
            print(f"  {key}: {sum(r[key] for r in part) / n:.2f}")
        passed = sum(1 for r in part if r["correctness"] >= 4)
        print(f"  correctness>=4: {passed}/{n} ({passed / n:.1%})")
    weak = [r for r in rows if r["correctness"] <= 2]
    if weak:
        print("\nLow correctness:")
        for r in weak:
            print(f"  [{r['id']}] {r['reason']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["generate", "judge", "summary"])
    args = parser.parse_args()
    {"generate": generate_answers, "judge": judge_answers, "summary": summary}[args.stage]()


if __name__ == "__main__":
    main()
