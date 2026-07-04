import json
import os
import urllib.error
import urllib.request
from typing import Any

from dotenv import load_dotenv


YANDEX_COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
SYSTEM_PROMPT = (
    "Ты AI-ассистент исследователя в материаловедении. Отвечай на русском языке, "
    "опирайся только на переданный контекст: документы, граф связей и гипотезы. "
    "Если данных недостаточно, явно назови пробелы и предложи, что уточнить."
)


def generate_llm_answer(query: str, context: dict[str, Any]) -> str | None:
    """Generate an answer with YandexGPT if credentials are configured."""
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "auto").strip().casefold()
    if provider in {"mock", "offline", "none", "disabled"}:
        return None

    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    model_name = os.getenv("YANDEX_GPT_MODEL", "yandexgpt-lite")
    timeout = float(os.getenv("YANDEX_TIMEOUT_SECONDS", "6"))

    if not api_key or not folder_id:
        return None

    payload = {
        "modelUri": f"gpt://{folder_id}/{model_name}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.25,
            "maxTokens": "900",
        },
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": _build_user_prompt(query, context)},
        ],
    }

    request = urllib.request.Request(
        YANDEX_COMPLETION_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
            "x-folder-id": folder_id,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    alternatives = data.get("result", {}).get("alternatives", [])
    if not alternatives:
        return None

    answer = alternatives[0].get("message", {}).get("text")
    if not answer:
        return None
    return str(answer).strip()


def _build_user_prompt(query: str, context: dict[str, Any]) -> str:
    return (
        f"Вопрос пользователя:\n{query}\n\n"
        "Контекст из системы:\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Сформируй короткий, полезный ответ для исследователя. "
        "Укажи найденные материалы, процессы, свойства, документы, связи и возможные гипотезы."
    )
