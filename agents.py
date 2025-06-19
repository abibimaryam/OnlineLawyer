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
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from pathlib import Path

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
    return "\n".join(results)

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
    MODEL_CACHE_DIR = Path.home() / ".my_models" / "sbert_large_mt_nlu_ru"
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sberbank-ai/sbert_large_mt_nlu_ru",
        cache_folder=str(MODEL_CACHE_DIR),  # явно указываем путь для кэширования
        device="cpu"
    )
    if os.path.exists(persist_dir):
        logger.info("Загружаем существующий индекс...")
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        vector_index = load_index_from_storage(storage_context)
    else:
        logger.info("Создаём новый индекс...")

        parser = LlamaParse(result_type="markdown") # type: ignore
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(
            input_dir="./data",
            file_extractor={".pdf": LlamaParse()}
        ).load_data()
        vector_index = VectorStoreIndex.from_documents(documents, embed_model=Settings.embed_model)
        vector_index.storage_context.persist(persist_dir=persist_dir)
    return vector_index.as_query_engine(llm=llm)

# === НОВАЯ ФУНКЦИЯ: conversation() для Telegram ===
async def conversation(user_input: str):
    """
    Принимает текст от пользователя из Telegram и возвращает историю диалога.
    """
    history = []
    hello = "Здравствуйте, расскажите о своей проблеме"
    history.append({"role": "assistant", "content": hello})
    history.append({"role": "user", "content": user_input})
    return history

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
    prompt = f"Проанализируй следующую историю переписки и сделай краткое содержание:\n{conv}"
    try:
        summarize_conv = await analyzer.run(prompt)
    except Exception as e:
        summarize_conv = f"Ошибка при создании краткой выжимки: {e}"
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
        tools_or_functions=[query_engine_tool, search_tool],
        llm=llm,
        system_prompt=(
            "Ты — юридический ИИ-агент. У тебя есть доступ к базе правовых документов (Конституция, кодексы и т.д.) "
            "Республики Узбекистан. Используй эти документы, чтобы выносить юридически обоснованный вердикт по входящему вопросу. "
            "Твой ответ должен быть кратким, чётким и ссылаться на релевантные статьи при необходимости. "
            "Всегда отвечай на русском языке. Используй только правовой стиль из Узбекистана."
        ),
    )
    prompt = f"На основании следующего описания ситуации вынеси юридический вердикт:\n{summarize_conv}"
    try:
        verdict = await query_engine_agent.run(prompt)
    except Exception as e:
        verdict = f"Ошибка при вынесении вердикта: {e}"
    return str(verdict)

# Оценка рисков
async def risk_estimate_and_forecast(summarize_conv, verdict):
    estimater = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[search_tool],
        llm=llm,
        system_prompt=(
            "Ты — юридический аналитик, специализирующийся на оценке правовых и репутационных рисков. "
            "На основе краткой выжимки диалога и юридического вердикта ты должен:\n"
            "- проанализировать ситуацию и определить потенциальные юридические, регуляторные и деловые риски,\n"
            "- оценить вероятность наступления последствий,\n"
            "- определить степень серьёзности риска (низкий, средний, высокий),\n"
            "- а также сделать прогноз дальнейшего развития ситуации с обоснованием.\n"
            "Если риски отсутствуют — сообщи об этом обоснованно.\n"
            "Всегда отвечай на русском языке, структурированно, с четкими пунктами."
        ),
    )
    prompt = (
        f"На основе следующей информации оцени возможные риски и сделай прогноз дальнейшего развития:\n"
        f"Краткая выжимка диалога:\n{summarize_conv}\n"
        f"Юридический вердикт:\n{verdict}\n"
        "Выведи список рисков с пояснениями и прогноз ситуации."
    )
    try:
        result = await estimater.run(prompt)
    except Exception as e:
        result = f"Ошибка при оценке рисков и прогнозе: {e}"
    return str(result)

# Проверка
async def review_func(verdict, risks):
    reviewer = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[search_tool],
        llm=llm,
        system_prompt=(
            "Ты — юридический рецензент. Проверь корректность юридического вердикта и оценки рисков.\n"
            "- Убедись, что вердикт содержит юридически обоснованные выводы и при необходимости ссылается на нормы законодательства Узбекистана.\n"
            "- Проверь, насколько логична и обоснованна оценка рисков, есть ли в ней структура, прогноз, степень серьёзности.\n"
            "- Укажи, есть ли ошибки, недостатки, противоречия или упущения.\n"
            "- Если всё корректно, напиши обоснованное подтверждение этого.\n"
            "‼️ В конце своего ответа обязательно укажи одну из строк:\n"
            "[ПРОВЕРКА: ПРОЙДЕНА] — если всё корректно\n"
            "[ПРОВЕРКА: НЕ ПРОЙДЕНА] — если есть ошибки\n"
            "Ответ структурируй по пунктам, на русском языке."
        ),
    )
    prompt = (
        f"Вот юридический вердикт:\n{verdict}\n"
        f"Вот анализ рисков:\n{risks}\n"
        "Проверь оба документа и напиши развернутую юридическую рецензию."
    )
    try:
        review = await reviewer.run(prompt)
        review_text = str(review).strip()
        passed = "проверка: пройдена" in review_text.lower()
    except Exception as e:
        review_text = f"Ошибка при проверке: {e}"
        passed = False
    return review_text, passed