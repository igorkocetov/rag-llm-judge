import json

from config import ANSWERS_PATH, GOLDEN_PATH, JUDGE_MODEL
from judge import JUDGE_PROMPT, UNANSWERABLE_NOTE, chat_json, read_jsonl

OUT_PATH = ANSWERS_PATH.parent / "judgments_adversarial.jsonl"

CASES = [
    {
        "name": "control: эталонный ответ",
        "id": "q021",
        "answer": "При Job падение одной дочерней корутины отменяет все остальные. При SupervisorJob корутины независимы.",
        "expect": lambda s: s["correctness"] >= 4 and s["groundedness"] >= 4 and s["completeness"] >= 4,
        "expect_text": "c,g,f >= 4",
    },
    {
        "name": "выдуманное утверждение (верный смысл + лишнее)",
        "id": "q021",
        "answer": (
            "При Job падение одной дочерней корутины отменяет все остальные. "
            "При SupervisorJob корутины независимы, а упавшая корутина автоматически "
            "перезапускается до трёх раз."
        ),
        "expect": lambda s: s["groundedness"] <= 3,
        "expect_text": "g <= 3",
    },
    {
        "name": "перепутанный смысл",
        "id": "q009",
        "answer": (
            "Dispatchers.IO предназначен для CPU-интенсивных задач, пул равен количеству ядер. "
            "Dispatchers.Default предназначен для I/O операций, пул до 64 потоков."
        ),
        "expect": lambda s: s["correctness"] <= 2 and s["groundedness"] <= 3,
        "expect_text": "c <= 2, g <= 3",
    },
    {
        "name": "верно, но неполно",
        "id": "q009",
        "answer": "Dispatchers.IO используется для I/O операций (сеть, БД, файлы).",
        "expect": lambda s: s["groundedness"] >= 4 and s["completeness"] <= 3,
        "expect_text": "g >= 4, f <= 3",
    },
    {
        "name": "лишний пункт в перечне",
        "id": "q005",
        "answer": "Порождающие (Creational), Структурные (Structural), Поведенческие (Behavioral) и Архитектурные (Architectural).",
        "expect": lambda s: s["groundedness"] <= 3,
        "expect_text": "g <= 3",
    },
    {
        "name": "галлюцинация вместо отказа",
        "id": "q002",
        "answer": "Нужно задать spring.kafka.consumer.group-id в application.yml и указать groupId в аннотации @KafkaListener.",
        "expect": lambda s: s["correctness"] <= 2 and s["groundedness"] <= 2,
        "expect_text": "c <= 2, g <= 2",
    },
]


def main() -> None:
    golden = {item["id"]: item for item in read_jsonl(GOLDEN_PATH)}
    answers = {row["id"]: row for row in read_jsonl(ANSWERS_PATH)}
    print(f"Judge model: {JUDGE_MODEL}")
    results = []
    for case in CASES:
        item = golden[case["id"]]
        base = answers[case["id"]]
        answerable = item.get("answerable", True)
        reference = item["reference_answer"] if answerable else "В документах нет ответа на этот вопрос"
        context = "\n\n---\n\n".join(c["text"] for c in base["chunks"])
        prompt = JUDGE_PROMPT.format(
            unanswerable_note="" if answerable else UNANSWERABLE_NOTE,
            question=base["question"],
            reference=reference,
            context=context,
            model_answer=case["answer"],
        )
        scores = chat_json(JUDGE_MODEL, prompt)
        ok = case["expect"](scores)
        results.append(ok)
        print(
            f"[{case['id']}] {case['name']}: "
            f"c={scores['correctness']} g={scores['groundedness']} f={scores['completeness']} "
            f"(ожидалось: {case['expect_text']}) -> {'OK' if ok else 'CHECK'}"
        )
        print(f"    reason: {scores['reason']}")
        with OUT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"case": case["name"], "id": case["id"], "answer": case["answer"], **scores}, ensure_ascii=False) + "\n")
    print(f"\nПройдено: {sum(results)}/{len(results)}")


if __name__ == "__main__":
    if OUT_PATH.exists():
        OUT_PATH.unlink()
    main()
