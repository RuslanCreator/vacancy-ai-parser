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

    max_turns = 5
    turns = 0

    while turns < max_turns:
        turns += 1
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

            if name not in FUNCTIONS:
                output = f"Ошибка: Инструмент '{name}' не существует."
            else:
                try:
                    args = json.loads(call.function.arguments)
                    output = FUNCTIONS[name](**args)
                except json.JSONDecodeError:
                    output = "Ошибка: Переданы некорректные JSON-аргументы."
                except Exception as e:
                    output = f"Ошибка выполнения инструмента: {str(e)}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(output, ensure_ascii=False),
                }
            )
    else:
        print("Агент остановлен: превышено максимальное количество шагов.")
