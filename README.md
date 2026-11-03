# RAG + LLM-as-a-Judge

Локальный RAG на Ollama и ChromaDB с последующей оценкой качества (golden set, метрики поиска, LLM-as-a-Judge).

## Результаты (golden set: 35 вопросов, 30 с ответом)

| Конфигурация | Hit rate@4 | MRR@4 | correctness | completeness | correctness >= 4 |
|--------------|------------|-------|-------------|--------------|------------------|
| Векторный поиск (800/100, k=4) | 0.900 | 0.883 | 4.50 | 4.27 | 26/30 |
| + reranking (pool=30) | 0.967 | 0.950 | 4.87 | 4.57 | 29/30 |

Генерация: `qwen3:4b`, судья: `qwen3.5:9b`, эмбеддинги: `bge-m3`. Судья сверен с ручной разметкой на 19 вопросах: 53 из 57 оценок совпали точно, 56 из 57 отличаются не более чем на балл. Оговорки: один прогон, малая выборка, `qwen3:4b` недетерминирован (часть прироста, в частности по q001, может быть шумом), калибровка судьи делалась на ответах без reranking. Подробности и разбор промахов: [reports/results.md](reports/results.md).

## Структура
- `config.py` — модели и параметры (переопределяются переменными окружения `GEN_MODEL`, `EMBED_MODEL`, `JUDGE_MODEL`, `CHUNK_MODE`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `RERANK`, `RERANK_MODEL`, `RERANK_POOL`)
- `check_ollama.py` — проверка подключения к генерации и эмбеддингам
- `ingest.py` — нарезка `.md` из `data/docs/` на чанки, эмбеддинги, запись в Chroma
- `ask.py` — вопрос, поиск top-k, ответ модели с источниками
- `eval_retrieval.py` — метрики поиска: hit rate@k и MRR@k по golden set
- `rerank.py` — cross-encoder (`BAAI/bge-reranker-v2-m3`): переупорядочение пула кандидатов после векторного поиска
- `judge.py` — этапы `generate` (ответы), `judge` (оценка correctness/groundedness/completeness), `summary` (сводка)
- `judge_adversarial.py` — проверка судьи на искусственных ошибочных ответах
- `data/docs/` — база знаний: 9 `.md`-руководств для подготовки к собеседованию мобильного разработчика (Kotlin Coroutines, RxJava, SOLID, паттерны и др.), сгенерированных с помощью Claude
- `data/golden.jsonl` — 35 вопросов (30 с ответом, 5 без ответа в документах)

## Установка (macOS)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ollama должна быть запущена. Модели:
```bash
ollama list
ollama pull bge-m3
```
Имя генеративной модели должно совпадать с `ollama list`. Если оно другое, задайте его:
```bash
export GEN_MODEL="имя_из_ollama_list"
```

## Запуск
```bash
python check_ollama.py
python ingest.py
python ask.py "Чем отличается launch от async в корутинах?"
```

## Оценка
```bash
python eval_retrieval.py --k 4
python eval_retrieval.py --k 4 --rerank --pool 30
python judge.py generate
python judge.py judge
python judge.py summary
python judge_adversarial.py
```
Базовая конфигурация: `CHUNK_MODE=fixed`, `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`, `TOP_K=4`, `GEN_MODEL=qwen3:4b`, `JUDGE_MODEL=qwen3.5:9b`. Индекс нужно пересоздавать (`python ingest.py`) при смене параметров чанков. Для повторной оценки удалите `data/judgments.jsonl` (скрипт пропускает уже оценённые id).

Reranking включается переменной `RERANK=1` (для `ask.py` и `judge.py generate`) или флагом `--rerank` (для `eval_retrieval.py`). Первый запуск скачивает модель (около 2 ГБ). Пул кандидатов по умолчанию 30. На golden set reranking поднял hit rate@4 с 0.900 до 0.967 (MRR@4 с 0.883 до 0.950); пул 10 эффекта не дал. Выборка маленькая (30 вопросов), подробности в [reports/results.md](reports/results.md).

Результаты экспериментов: [reports/results.md](reports/results.md), сверка судьи с ручной разметкой: [reports/check_handle.md](reports/check_handle.md).

Ограничения: выборка небольшая, ручная разметка одним человеком; groundedness проверяется только по найденным чанкам; способность судьи ловить галлюцинации проверена на 6 синтетических случаях.

## План
1. [x] Каркас: подключение, индексация, ответ с источниками
2. [x] Golden set: 35 вопросов с эталонными ответами и нужным фрагментом (`data/golden.jsonl`)
3. [x] Метрики поиска: hit rate, MRR
4. [x] LLM-as-a-Judge: корректность, опора на контекст, полнота (JSON)
5. [x] Сверка судьи с ручной разметкой: доля совпадений, pass/fail (корреляция и бутстреп-доверительный интервал не считались)
6. [ ] Эксперименты: размер чанка (сделано), top-k (сделано), reranking (сделано для retrieval), нарезка по заголовкам (`CHUNK_MODE=heading`), вопросы без ответа в документах (сделано)
