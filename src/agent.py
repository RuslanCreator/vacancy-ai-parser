import json
import os

from openai import OpenAI
from src.tools import TOOLS, get_vacancies, notify_user

MODEL = "deepseek-v4-flash-free"
SYSTEM_MESSAGE = (
    "Ты -- ассистент по поиску работы. Найди вакансии по запросу "
    "пользователя через get_vacancies, отбери действительно подходящие "
    "и отправь каждую. В конце коротко отчитайся."
)
FUNCTIONS = {"get_vacancies": get_vacancies, "notify_user": notify_user}


def run_agent(user_request):
    client = OpenAI(
        api_key=os.getenv("OPENCODE_API_KEY"),
        base_url="https://opencode.ai/zen/v1",
    )
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": user_request},
    ]
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        messages.append(message)
        if not message.tool_calls:
            print(message.content)
            break
        for call in message.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            output = FUNCTIONS[name](**args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(output, ensure_ascii=False),
                }
            )
