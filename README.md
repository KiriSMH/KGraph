# Научный клубок

MVP поисково-аналитической системы для материаловедения по треку «Научный клубок».

Пользователь задает научный вопрос естественным языком, а система возвращает:

- аналитический ответ агента;
- релевантные документы;
- граф связей между материалами, процессами, свойствами, экспериментами и источниками;
- гипотезы и пробелы в данных;
- уточняющие вопросы.

Проект сделан как demo-safe приложение: если Neo4j, YandexGPT или embeddings недоступны, сайт не падает, а использует локальные mock-данные и offline-agent.

## Команда

- Лакпажап Дан-Хаяа;
- Щетинникова Любовь;
- Самохвалов Кирилл;
- Хадралинова Полина.

## Архитектура

```text
Frontend Web UI
  |
  v
FastAPI backend
  |
  +-- /chat        -> agent_service
  +-- /upload      -> file upload + retrieval indexing
  +-- /search      -> uploaded chunks + mock documents
  +-- /graph       -> Neo4j if available, mock graph fallback
  +-- /hypotheses  -> mock hypotheses
  |
  +-- YandexGPT adapter      optional
  +-- Yandex embeddings      optional
  +-- Neo4j knowledge graph  optional
  |
  v
data/*.json + data/uploads/*
```

## Стек

- Python 3.10+;
- FastAPI;
- HTML/CSS/JS frontend без сборки;
- mock JSON data;
- optional Neo4j;
- optional YandexGPT / Yandex embeddings;
- optional Qdrant in-memory для vector search.

## Быстрый запуск демо

### 1. Backend

```powershell
cd "C:\Users\samoh\OneDrive\Рабочий стол\Xakaton\science-knot\backend"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 18080
```

Swagger UI:

```text
http://127.0.0.1:18080/docs
```

Health check:

```text
http://127.0.0.1:18080/health
```

### 2. Frontend

Во втором терминале:

```powershell
cd "C:\Users\samoh\OneDrive\Рабочий стол\Xakaton\science-knot"
.\backend\.venv\Scripts\python.exe -m http.server 5500 -d frontend-web
```

Открыть:

```text
http://127.0.0.1:5500
```

## Стабильный режим для защиты

Если внешние ключи заблокированы, в `.env` можно поставить:

```env
LLM_PROVIDER=mock
```

Тогда backend не будет ждать внешний GPT и будет использовать offline-agent.

Даже без Neo4j и YandexGPT работает полный сценарий:

```text
запрос -> ответ -> документы -> граф -> гипотезы -> загрузка файлов
```

## Демо-запросы

- Что известно про Ti-6Al-4V после закалки?
- Какие режимы повышали прочность алюминиевых сплавов?
- Что делали для повышения коррозионной стойкости?
- Где есть пробелы по лазерной обработке?
- Какие эксперименты связаны с Inconel 718?

## Что сейчас работает

- `GET /health`;
- `GET /documents`;
- `POST /upload` — сохранение PDF/TXT/DOCX/JSON и индексация текста;
- `POST /search` — поиск по загруженным чанкам и mock-документам;
- `POST /graph` — Neo4j при наличии базы, иначе быстрый fallback на `data/graph.json`;
- `POST /hypotheses`;
- `POST /chat` — единый ответ агента;
- frontend-web с загрузкой файлов, поиском, графом, документами и гипотезами;
- offline-agent, который формирует аналитический ответ без внешнего LLM.

## Neo4j

Backend сначала пробует взять граф из Neo4j:

```text
backend/app/services/graph_service.py
  -> kg/neo4j_client.py
  -> kg/queries.py
```

Если Neo4j не запущен, backend быстро возвращает mock-граф из `data/graph.json`.

Проверка Neo4j:

```powershell
cd "C:\Users\samoh\OneDrive\Рабочий стол\Xakaton\science-knot"
.\backend\.venv\Scripts\python.exe -c "from kg.neo4j_client import Neo4jClient; c=Neo4jClient(); print(c.read('RETURN 1 AS ok')); c.close()"
```

Если Neo4j работает:

```text
[{'ok': 1}]
```

Импорт demo-графа:

```powershell
.\backend\.venv\Scripts\python.exe scripts\build_graph.py
.\backend\.venv\Scripts\python.exe scripts\import_json.py data\examples\example_materials.json
```

## Retrieval / NLP

Загрузка источников:

```text
PDF/TXT/DOCX/JSON
  -> extraction text
  -> chunk_text()
  -> Yandex embeddings if available
  -> Qdrant in-memory if available
  -> local chunk search fallback
```

Если Yandex embeddings недоступны, система продолжает искать по текстовым чанкам локально.

## YandexGPT

Файл `.env`:

```env
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
LLM_PROVIDER=auto
YANDEX_GPT_MODEL=yandexgpt-lite
YANDEX_TIMEOUT_SECONDS=6
YANDEX_EMBEDDING_DOC_MODEL=text-search-doc/latest
YANDEX_EMBEDDING_QUERY_MODEL=text-search-query/latest
```

Если доступ к YandexGPT заблокирован, использовать:

```env
LLM_PROVIDER=mock
```

## Схема связей Knowledge Graph

Для графа ориентируемся на такие отношения:

- `USES_MATERIAL`: `Process -> Material`;
- `OPERATES_AT_CONDITION`: `Process -> Property`, `Equipment -> Property`;
- `PRODUCES_OUTPUT`: `Process -> Material`;
- `DESCRIBED_IN`: `Experiment | Process | Material | Property | Equipment | Expert | Facility -> Publication`;
- `VALIDATED_BY`: `Property | Process | Material -> Experiment | Expert`;
- `CONTRADICTS`: `Experiment <-> Experiment`, `Experiment <-> Publication`, `Property <-> Property`, `Process <-> Process`, `Publication <-> Publication`.

Правило для противоречий: противоречие отмечается только если совпадают материал, режим, условия эксперимента и измеряемое свойство. Если отличаются состав материала, концентрации, температура, оборудование или методика, разное поведение свойства считается не конфликтом, а ожидаемым различием условий.

## Источники данных

Эти ресурсы можно использовать как источники для ручной или автоматической загрузки документов:

- ResearchGate;
- eLIBRARY;
- SpringerLink;
- Google Patents;
- MDPI;
- CyberLeninka;
- Wiley Online Library;
- ScienceDirect.

Практическое использование в MVP:

- скачать/сохранить статью или фрагмент текста;
- загрузить PDF/TXT/DOCX/JSON через блок «Источники»;
- задать вопрос по материалу, режиму и свойству;
- система покажет найденные чанки, графовые связи и пробелы.

В текущем MVP мы не парсим внешние сайты автоматически. Это снижает риск поломок, блокировок и юридических проблем перед сдачей: пользователь сам загружает доступный ему файл или текст.

## Что можно заменить после демо

- `data/graph.json` -> Neo4j;
- local chunk search -> Qdrant/Chroma/Yandex embeddings;
- offline-agent -> полноценный LLM-agent;
- mock documents -> реальные документы хакатона;
- mock hypotheses -> гипотезы, построенные по графу и источникам.
