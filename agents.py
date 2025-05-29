import os
import asyncio
import logging
from dotenv import load_dotenv
from llama_index.llms.groq import Groq
from llama_index.core.agent.workflow import AgentWorkflow
from duckduckgo_search import DDGS
from llama_index.core.workflow import Context
from llama_parse import LlamaParse
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка .env
load_dotenv()

# Инициализация LLM с использованием Groq
llm = Groq(
    model="llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
)

# Поисковый инструмент
def search_tool(query: str) -> str:
    with DDGS() as ddgs:
        results = [r["body"] for r in ddgs.text(query, max_results=3)]
    return "\n\n".join(results)

# Агент-интервьюер
interviewer = AgentWorkflow.from_tools_or_functions(
    tools_or_functions=[search_tool],
    llm=llm,
    system_prompt=(
        "Ты — профессиональный юрист. Твоя задача — оказывать первичную юридическую консультацию пользователю, "
        "задавая уточняющие вопросы, чтобы понять суть ситуации. Общайся кратко, по существу, без эмоций. "
        "Если нужны сведения, которых нет, используй поисковик. Не давай медицинских или психологических советов."
    ),
)
ctx = Context(interviewer)

# Инициализация или загрузка векторной базы
def init_query_engine():
    persist_dir = "./vector_index"

    if os.path.exists(persist_dir):
        logger.info("Загружаем существующий индекс...")
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        vector_index = load_index_from_storage(storage_context)
    else:
        logger.info("Создаём новый индекс...")
        parser = LlamaParse(result_type="markdown")
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()

        embed_model = resolve_embed_model("local:BAAI/bge-m3")
        vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
        vector_index.storage_context.persist(persist_dir=persist_dir)

    return vector_index.as_query_engine(llm=llm)

# Основной диалоговый цикл
async def conversation():
    history = []
    hello = "Здравствуйте, расскажите о своей проблеме"
    print(f"Юрист: {hello}")
    history.append({"role": "user", "content": hello})

    while True:
        user_input = input("Вы: ").strip()
        if user_input.lower() in ["выход", "exit", "quit"]:
            print("Юрист: До свидания!")
            return history

        history.append({"role": "user", "content": user_input})
        try:
            response = await interviewer.run(user_input, ctx=ctx)
            response = str(response)
            print(f"Юрист: {response}")
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"[Ошибка] {e}")

# Анализ истории
async def analyze(conv):
    analyzer = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[search_tool],
        llm=llm,
        system_prompt=(
            "Ты — умный помощник, который анализирует историю переписки пользователя с ИИ. "
            "На основе диалога ты должен сделать краткую выжимку основных тем, вопросов и выводов. "
            "Если были даны советы или действия, кратко опиши их."
        )
    )

    prompt = f"Проанализируй следующую историю переписки и сделай краткое содержание:\n\n{conv}"
    summarize_conv = await analyzer.run(prompt)
    return str(summarize_conv)

# Вынесение юридического вердикта
async def pass_a_verdict(summarize_conv):
    query_engine = init_query_engine()
    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="legal_documents_search",
            description="Поиск и извлечение информации из Конституции, кодексов и других правовых документов Узбекистана."
        ),
    )

    query_engine_agent = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[query_engine_tool],
        llm=llm,
        system_prompt=(
            "Ты — юридический ИИ-агент. У тебя есть доступ к базе правовых документов (Конституция, кодексы и т.д.) "
            "Республики Узбекистан. Используй эти документы, чтобы выносить юридически обоснованный вердикт по входящему вопросу. "
            "Твой ответ должен быть кратким, чётким и ссылаться на релевантные статьи при необходимости."
        ),
    )

    prompt = f"На основании следующего описания ситуации вынеси юридический вердикт:\n\n{summarize_conv}"
    verdict = await query_engine_agent.run(prompt)
    return str(verdict)

# Оценка рисков
async def risk_estimate(summarize_conv, verdict):
    estimater = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[search_tool],
        llm=llm,
        system_prompt=(
            "Ты — юридический аналитик, специализирующийся на оценке правовых и репутационных рисков. "
            "На основе краткой выжимки диалога и юридического вердикта ты должен проанализировать ситуацию и определить:\n"
            "- потенциальные юридические, регуляторные и деловые риски,\n"
            "- вероятность наступления последствий,\n"
            "- степень серьёзности риска (низкий, средний, высокий).\n"
            "Если риски отсутствуют — сообщи об этом обоснованно."
        ),
    )

    prompt = (
        f"На основе следующей информации оцени возможные риски:\n\n"
        f"Краткая выжимка диалога:\n{summarize_conv}\n\n"
        f"Юридический вердикт:\n{verdict}\n\n"
        "Выведи список рисков с пояснениями."
    )

    risks = await estimater.run(prompt)
    return str(risks)

# Главная функция
async def main():
    conv = await conversation()
    summarize_conv = await analyze(conv=conv)
    print("\nКраткая выжимка:\n", summarize_conv)

    verdict = await pass_a_verdict(summarize_conv=summarize_conv)
    print("\nЮридический вердикт:\n", verdict)

    risks = await risk_estimate(summarize_conv=summarize_conv, verdict=verdict)
    print("\nОценка рисков:\n", risks)

    # Сохраняем результаты в файл (опционально)
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write(f"Краткая выжимка:\n{summarize_conv}\n\n")
        f.write(f"Юридический вердикт:\n{verdict}\n\n")
        f.write(f"Оценка рисков:\n{risks}\n")

if __name__ == "__main__":
    asyncio.run(main())