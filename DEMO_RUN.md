# DEMO RUN

Короткая инструкция для показа проекта.

## 1. Стабильный режим без внешнего GPT

В `.env` можно поставить:

```env
LLM_PROVIDER=mock
```

Так демо не зависит от заблокированных API-ключей.

## 2. Запустить backend

```powershell
cd "C:\Users\samoh\OneDrive\Рабочий стол\Xakaton\science-knot\backend"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 18080
```

Проверка:

```text
http://127.0.0.1:18080/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## 3. Запустить frontend

Во втором терминале:

```powershell
cd "C:\Users\samoh\OneDrive\Рабочий стол\Xakaton\science-knot"
.\backend\.venv\Scripts\python.exe -m http.server 5500 -d frontend-web
```

Открыть:

```text
http://127.0.0.1:5500
```

## 4. Основной сценарий показа

Ввести запрос:

```text
Что известно про Ti-6Al-4V после закалки?
```

Показать:

- ответ агента;
- уточняющие вопросы;
- связанные документы;
- граф связей;
- потенциальные гипотезы и пробелы.

## 5. Проверить загрузку файла

Загрузить небольшой `.txt`, `.pdf`, `.docx` или `.json`.

Ожидаемо:

- файл появляется в блоке «Источники»;
- статус показывает, что файл загружен и проиндексирован;
- следующие запросы учитывают текст загруженного файла.

## 6. Проверить backend вручную

```powershell
cd "C:\Users\samoh\OneDrive\Рабочий стол\Xakaton\science-knot\backend"
.\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); r=c.post('/chat', json={'message':'Что известно про Ti-6Al-4V после закалки?','session_id':'demo'}); print(r.status_code); print(r.json().keys())"
```

Ожидаемо:

```text
200
dict_keys(['answer', 'follow_up_questions', 'documents', 'graph', 'hypotheses'])
```

## 7. Что говорить на защите

Короткая формулировка:

```text
Приложение работает в demo-safe режиме: даже если Neo4j или внешний LLM недоступны,
backend не падает, а использует локальные mock-данные, local retrieval и offline-agent.
Архитектура уже содержит адаптеры для Neo4j, YandexGPT и Yandex embeddings.
```
