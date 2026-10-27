"""Server-only OpenRouter client; never includes response bodies in errors."""
import json
import os
import socket
import urllib.error
import urllib.request

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class ModelError(Exception):
    pass


def complete(messages):
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ModelError("Модель ще не налаштована. Власнику потрібно додати OPENROUTER_API_KEY у секрети сервера.")
    payload = json.dumps({"model": "openrouter/free", "messages": messages,
                          "temperature": 0.2, "max_tokens": 1200}).encode("utf-8")
    request = urllib.request.Request(ENDPOINT, data=payload, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
        "X-Title": "LystOK Letter Assistant",
    }, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read(1_000_001))
        text = data["choices"][0]["message"]["content"]
        if not isinstance(text, str) or not text.strip() or len(text) > 15000:
            raise ModelError("Модель повернула порожню або завелику відповідь. Спробуйте ще раз.")
        if key in text:
            raise ModelError("Відповідь не пройшла перевірку безпеки.")
        if data["choices"][0].get("finish_reason") == "length":
            raise ModelError("Модель не завершила лист. Спробуйте скоротити чернетку.")
        if not text.strip().startswith("Тема:") or "\n" not in text.strip():
            raise ModelError("Модель не сформувала лист у потрібному форматі. Спробуйте ще раз.")
        return text.strip()
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise ModelError("OpenRouter не прийняв ключ або доступ до моделі. Власнику потрібно перевірити налаштування.") from None
        if error.code in (402, 429):
            raise ModelError("Досягнуто ліміту OpenRouter. Спробуйте пізніше.") from None
        raise ModelError("OpenRouter тимчасово недоступний. Спробуйте пізніше.") from None
    except (urllib.error.URLError, TimeoutError, socket.timeout):
        raise ModelError("Не вдалося з’єднатися з моделлю. Спробуйте пізніше.") from None
    except (ValueError, KeyError, IndexError, TypeError):
        raise ModelError("Модель повернула неочікувану відповідь. Спробуйте ще раз.") from None
