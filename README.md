# Научный клубок

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
    +-- search_service  — keyword search по документам
    +-- graph_service   — извлечение подграфа
    +-- data_service    — безопасное чтение JSON
    +-- vector_service  — заглушка Qdrant/Chroma
    +-- llm_service     — заглушка LLM
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
- `POST /search` с простым ранжированием;
- `POST /graph` с выборкой связанных узлов и рёбер;
- `POST /hypotheses` с фильтрацией по материалу или свойству;
- `POST /chat`, объединяющий ответ, документы, граф и гипотезы;
- web frontend с поиском, реальной отправкой файлов в backend, чатом, графом, документами и гипотезами;
- Streamlit-интерфейс как запасной вариант;
- безопасная обработка отсутствующих и некорректных JSON-файлов.

## Будущие интеграции

Точки замены изолированы в сервисном слое:

- JSON graph → Neo4j в `graph_service.py`;
- keyword search → Qdrant/Chroma в `search_service.py` и `vector_service.py`;
- mock agent → LLM agent через `llm_service.py`;
- mock data → реальные документы хакатона через `data_service.py` или ingestion pipeline.

Контракты API и Streamlit-интерфейс при этих заменах можно сохранить.
