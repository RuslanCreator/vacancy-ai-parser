from dotenv import load_dotenv
from src.agent import run_agent

load_dotenv()


def main():
    print("Hello from vacancy-ai-parser!")
    run_agent("Найди вакансии на Python, грейд Middle")


if __name__ == "__main__":
    main()
