import os
import asyncio
from dotenv import load_dotenv
from llama_index.llms.groq import Groq
from llama_index.core.agent.workflow import AgentWorkflow
from duckduckgo_search import DDGS
from llama_index.core.workflow import Context
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent

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

# Создание агента интервьюера
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




async def analyze(conv):
    # Создание агента анализатора
    analyzer = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[search_tool],
        llm=llm,
        system_prompt = (
        "Ты — умный помощник, который анализирует историю переписки пользователя с ИИ. "
        "На основе диалога ты должен сделать краткую выжимку основных тем, вопросов и выводов. "
        "Если были даны советы или действия, кратко опиши их."
    , )
     )

    prompt = f"Проанализируй следующую историю переписки и сделай краткое содержание:\n\n{conv}"
    summarize_conv=await analyzer.run(prompt)
    return str(summarize_conv)




parser = LlamaParse(result_type="markdown")

file_extractor = {".pdf": parser}
documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()

embed_model = resolve_embed_model("local:BAAI/bge-m3")
vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine = vector_index.as_query_engine(llm=llm)

async def pass_a_verdict(summarize_conv):
    verdict=""


    # result=query_engine.query("Какая первая статья конституции Республики Узбекистан?")
    # print(result)
    # Инструмент для агента
    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="legal_documents_search",
            description="Поиск и извлечение информации из Конституции, кодексов и других правовых документов Узбекистана."
        ),
    )

    # Агент, который выносит вердикт с опорой на правовые документы (RAG)
    query_engine_agent = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[query_engine_tool],  # передаём сам объект, а не список из него
        llm=llm,
        system_prompt=(
            "Ты — юридический ИИ-агент. У тебя есть доступ к базе правовых документов (Конституция, кодексы и т.д.) "
            "Республики Узбекистан. Используй эти документы, чтобы выносить юридически обоснованный вердикт по входящему вопросу. "
            "Твой ответ должен быть кратким, чётким и ссылаться на релевантные статьи при необходимости."
        ),
    )
    # Формируем запрос агенту
    prompt = f"На основании следующего описания ситуации вынеси юридический вердикт:\n\n{summarize_conv}"

    # Запуск агента
    verdict = await query_engine_agent.run(prompt)

    return str(verdict)


async def risk_estimate(summarize_conv,verdict):
    # Создание агента риск оценщика
    estimater = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[search_tool],
        llm=llm,
        system_prompt = (
        "Ты — юридический аналитик, специализирующийся на оценке правовых и репутационных рисков. "
        "На основе краткой выжимки диалога и юридического вердикта ты должен проанализировать ситуацию и определить:\n"
        "- потенциальные юридические, регуляторные и деловые риски,\n"
        "- вероятность наступления последствий,\n"
        "- степень серьёзности риска (низкий, средний, высокий).\n"
        "Если риски отсутствуют — сообщи об этом обоснованно."
    ), 
    ) 
       # Формируем запрос для анализа рисков
    prompt = (
        f"На основе следующей информации оцени возможные риски:\n\n"
        f"Краткая выжимка диалога:\n{summarize_conv}\n\n"
        f"Юридический вердикт:\n{verdict}\n\n"
        "Выведи список рисков с пояснениями."
    )

    # Запускаем агента
    risks = await estimater.run(prompt)
    return str(risks)



async def main():
    conv = await conversation() # В conv хранится история агента интервьюера с юзером 
    # print(conv)
    summarize_conv=await analyze(conv=conv) # в summarize_conv краткая выжимка диалого
    print("Краткая выжимка:")
    print(summarize_conv)
    verdict=await pass_a_verdict(summarize_conv=summarize_conv) # в verdict хранится вердикт
    print("Юридический вердикт:")
    print(verdict)
    risks=await risk_estimate(summarize_conv=summarize_conv,verdict=verdict) # в risks хранятся риски
    print("Оценка рисков:")
    print(risks)






if __name__ == "__main__":
    asyncio.run(main())
