# Научный клубок MVP

## Описание

«Научный клубок» — MVP поисково-аналитической системы для материаловедения. Пользователь задаёт вопрос естественным языком, а система возвращает краткий ответ, релевантные документы, фрагмент графа знаний, уточняющие вопросы и потенциальные исследовательские гипотезы.

Текущая версия полностью работает на локальных mock JSON-данных и демонстрирует сквозной сценарий frontend → backend → данные.

## Архитектура

```text
Frontend Web UI
    |
    v
FastAPI endpoints
    |
    +-- agent_service   — собирает единый ответ
    +-- agent           — стабильный контракт agent.chat()
    +-- search_service  — semantic search по загрузкам + keyword search по mock-документам
    +-- graph_service   — извлечение подграфа
    +-- data_service    — безопасное чтение JSON
    +-- vector_service  — retrieval.py-интеграция: PDF/TXT/DOCX/JSON -> chunks -> embeddings/Qdrant
    +-- llm_service     — optional YandexGPT adapter с offline fallback
    |
    v
data/*.json
```

## Стек

- Python 3.10+
- FastAPI + Uvicorn
- Streamlit
- HTML/CSS/JS frontend без сборки
- JSON mock data

## Как запустить backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 18080
```

Swagger UI: <http://127.0.0.1:18080/docs>

Проверка состояния: <http://127.0.0.1:18080/health>

## Как запустить frontend для демо

Рекомендуемый интерфейс для показа команде:

```bash
cd science-knot
python -m http.server 5500 -d frontend-web
```

Интерфейс: <http://127.0.0.1:5500>

Backend должен быть запущен на `http://127.0.0.1:18080`.

## Как запустить Streamlit frontend

Запасной Streamlit-интерфейс:

Во втором терминале:

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Интерфейс: <http://localhost:8501>

## Демо-запросы

- Что известно про Ti-6Al-4V после закалки?
- Какие режимы повышали прочность алюминиевых сплавов?
- Что делали для повышения коррозионной стойкости?
- Где есть пробелы по лазерной обработке?
- Какие эксперименты связаны с Inconel 718?

## Что сейчас работает

- `GET /health` и `GET /documents`;
- `POST /upload` для сохранения пользовательских файлов в `data/uploads/`;
- `POST /search` с поиском по загруженным файлам и mock-документам;
- `POST /graph` с выборкой связанных узлов и рёбер;
- `POST /hypotheses` с фильтрацией по материалу или свойству;
- `POST /chat`, объединяющий ответ, документы, граф и гипотезы;
- web frontend с поиском, реальной отправкой файлов в backend, чатом, графом, документами и гипотезами;
- Streamlit-интерфейс как запасной вариант;
- безопасная обработка отсутствующих и некорректных JSON-файлов.
- offline-agent с аналитическим ответом, если внешний LLM недоступен.

## Будущие интеграции

Точки замены изолированы в сервисном слое:

- JSON graph → Neo4j в `graph_service.py` через модуль `kg/`;
- keyword search → Qdrant/Chroma в `search_service.py` и `vector_service.py`;
- mock agent → LLM agent через `llm_service.py`;
- mock data → реальные документы хакатона через `data_service.py` или ingestion pipeline.

Контракты API и Streamlit-интерфейс при этих заменах можно сохранить.

## Интеграция с Neo4j-модулем

В проект добавлен модуль `kg/` для работы с Neo4j. Backend уже умеет пробовать брать подграф из Neo4j через этот модуль:

```text
POST /graph
POST /chat
  -> backend/app/services/graph_service.py
  -> kg/neo4j_client.py
  -> kg/queries.py
```

Если Neo4j не настроен, нет пароля или база недоступна, backend автоматически возвращается к mock-графу из `data/graph.json`, поэтому демо продолжает работать.

Чтобы включить Neo4j:

1. Скопировать `.env.example` в `.env`.
2. Заполнить `NEO4J_PASSWORD`.
3. Установить зависимости из `backend/requirements.txt`.
4. Импортировать данные в Neo4j через скрипты из `scripts/`.

## Подключение YandexGPT

Backend умеет использовать YandexGPT через Yandex AI Studio. Если ключи не заданы или API недоступен, система автоматически использует mock-ответ агента.

Чтобы включить YandexGPT:

1. Скопировать `.env.example` в `.env`.
2. Заполнить:

```text
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_GPT_MODEL=yandexgpt-lite
```

3. Перезапустить backend.

После этого `POST /chat` будет собирать контекст из документов, графа и гипотез, а текст ответа будет формироваться через YandexGPT.

## Интеграция NLP / retrieval

В `backend/app/services/retrieval.py` добавлена адаптация NLP-модуля участника:

```text
PDF/TXT/DOCX/JSON
  -> извлечение текста
  -> chunk_text()
  -> embeddings через Yandex Foundation Models
  -> Qdrant in-memory
  -> semantic_search()
```

Если `YANDEX_API_KEY`, `YANDEX_FOLDER_ID` или `qdrant-client` недоступны, backend не падает: включается локальный fallback-поиск по чанкам. Поэтому демо продолжает работать даже без embeddings.

Чтобы включить настоящий semantic search:

1. Установить зависимости из `backend/requirements.txt`.
2. Добавить в `.env`:

```text
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_EMBEDDING_DOC_MODEL=text-search-doc/latest
YANDEX_EMBEDDING_QUERY_MODEL=text-search-query/latest
```

3. Перезапустить backend.
4. Загрузить PDF/TXT/DOCX/JSON на сайте через блок «Источники».

После загрузки `/chat` и `/search` будут учитывать текст загруженных файлов.

## Demo-safe режим

Если внешние API заблокированы, в `.env` можно указать:

```text
LLM_PROVIDER=mock
```

В этом режиме backend не обращается к YandexGPT и сразу использует offline-agent. Приложение всё равно показывает ответ, документы, граф, гипотезы и уточняющие вопросы.

## Схема отношений

Для Knowledge Graph используем такие типы связей:

- `USES_MATERIAL`: `Process -> Material`;
- `OPERATES_AT_CONDITION`: `Process -> Property`, `Equipment -> Property`;
- `PRODUCES_OUTPUT`: `Process -> Material`;
- `DESCRIBED_IN`: `Experiment | Process | Material | Property | Equipment | Expert | Facility -> Publication`;
- `VALIDATED_BY`: `Property | Process | Material -> Experiment | Expert`;
- `CONTRADICTS`: только при совпадении материала, режима, условий и свойства.
