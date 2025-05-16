import os
import asyncio
from dotenv import load_dotenv
from llama_index.llms.groq import Groq
from llama_index.core.agent.workflow import AgentWorkflow
from duckduckgo_search import DDGS
from llama_index.core.workflow import Context

# Загрузка .env
load_dotenv()

# Инициализация LLM с использованием Groq
llm = Groq(
    model="llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
)

def search_tool(query: str) -> str:
        with DDGS() as ddgs:
            results = [r["body"] for r in ddgs.text(query, max_results=3)]
        return "\n\n".join(results)

# Создание агента 
interviewer = AgentWorkflow.from_tools_or_functions(
    tools_or_functions=[search_tool],
    llm=llm,
    system_prompt = (
    "Ты — профессиональный юрист. Твоя задача — оказывать первичную юридическую консультацию пользователю, "
    "задавая уточняющие вопросы, чтобы понять суть ситуации. Общайся кратко, по существу, без эмоций. "
    "Если нужны сведения, которых нет, используй поисковик. Не давай медицинских или психологических советов."
),
)

ctx = Context(interviewer)


# Основной диалоговый цикл
async def conversation():
    history = []
    hello="Здравствуйте, расскажите о своей проблеме"
    print(f"Юрист:{hello}")
    history.append({"role": "user", "content": hello})
    while True:
        user_input = input("Вы: ").strip()
        if user_input.lower() in ["выход", "exit", "quit"]:
            print("Юрист: До свидания!")
            # выводит историю
            # print(history)
            return history

        history.append({"role": "user", "content": user_input})
        try:
            response = await interviewer.run(user_input,ctx=ctx)
            response=str(response)
            print(f"Юрист: {response}")
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"[Ошибка] {e}")
     
async def main():
    conv = await conversation()
    # print(conv)

if __name__ == "__main__":
    asyncio.run(main())
