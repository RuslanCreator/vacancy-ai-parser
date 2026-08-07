import json
import os
import time

import requests

SEEN_FILE = "seen_vacancies.json"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()


def save_seen(seen_set):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_set), f, ensure_ascii=False)


def get_vacancies(text: str, salary_from: float = 0, limit: int = 5):
    salary_from = int(salary_from or 0)
    url = "https://opendata.trudvsem.ru/api/v1/vacancies"
    params = {"text": text, "limit": limit, "offset": 0}
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=60)
            break
        except requests.exceptions.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)
    data = response.json()
    raw = data.get("results", {}).get("vacancies", [])
    result = []
    for item in raw:
        vac = item.get("vacancy", {})
        salary_min = int(vac.get("salary_min") or 0)
        if salary_min < salary_from:
            continue
        result.append(
            {
                "id": vac.get("id"),
                "name": vac.get("job-name"),
                "salary": vac.get("salary"),
                "company": vac.get("company", {}).get("name"),
                "region": vac.get("region", {}).get("name"),
                "url": vac.get("vac_url"),
            }
        )
    return result


def notify_user(vacancy):
    seen = load_seen()
    if vacancy["id"] in seen:
        return "Пропущено: вакансия уже отправлялась"
    text = (
        f"🔎 {vacancy['name']}\n"
        f"🏢 {vacancy['company']}\n"
        f"💰 {vacancy['salary']}\n"
        f"📍 {vacancy['region']}\n"
        f"🔗 {vacancy['url']}"
    )
    url = f"https://api.telegram.org/bot{os.getenv('TG_TOKEN')}/sendMessage"
    response = requests.post(
        url, json={"chat_id": os.getenv("TG_CHAT_ID"), "text": text}, timeout=30
    )
    if not response.json().get("ok"):
        raise RuntimeError("Telegram не принял сообщение: " + response.text)
    seen.add(vacancy["id"])
    save_seen(seen)
    return "Отправлено"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_vacancies",
            "description": "Найти вакансии по ключевому слову и минимальной зарплате",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Ключевое слово, например 'python разработчик'"
                        ", не содержит зарплаты",
                    },
                    "salary_from": {
                        "type": "integer",
                        "description": "Минимальная зарплата в рублях",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notify_user",
            "description": "Отправить подходящую вакансию пользователю в Telegram",
            "parameters": {
                "type": "object",
                "properties": {
                    "vacancy": {
                        "type": "object",
                        "description": "Объект вакансии из get_vacancies",
                    },
                },
                "required": ["vacancy"],
            },
        },
    },
]
