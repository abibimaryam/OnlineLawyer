import asyncio
import logging
import aiosqlite
import datetime
#from config import TOKEN 
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.enums import ParseMode
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery # ReplyKeyboardMarkup 
from aiogram.utils.keyboard import InlineKeyboardBuilder #ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
# from aiogram.types import ReplyKeyboardRemove
from aiogram.types import BotCommandScopeChat

import os
from dotenv import load_dotenv

load_dotenv()

class UserRegistrationStates(StatesGroup):
    first_name = State()
    second_name = State()
    patronymic = State()
    phone = State()
    email = State()
    
class LawyerRegistrationStates(StatesGroup):
    first_name = State()
    second_name = State()
    patronymic = State()
    specialization = State()
    phone = State()
    email = State()

user_lawyer =  InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Пользователь', callback_data='user_register'), InlineKeyboardButton(text='Юрист', callback_data='lawyer_register')]
    ]
)

class YourStates(StatesGroup):
    waiting_for_question = State()

# Состояние для юриста, который отвечает на вопрос
class AnsweringStates(StatesGroup):
    waiting_for_answer = State()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token= os.getenv('LAWYER_BOT_TOKEN'))
# Диспетчер
dp = Dispatcher(storage=MemoryStorage())

# Команды
async def set_personal_commands(bot: Bot, user_id: int):
    async with aiosqlite.connect("telegram_data_base.db") as db:
        user = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        is_user = await user.fetchone()
        lawyer = await db.execute("SELECT id FROM lawyers WHERE id = ?", (user_id,))
        is_lawyer = await lawyer.fetchone()

    if is_user:
        commands = [
            types.BotCommand(command="start", description="Запуск бота"),
            types.BotCommand(command="ask", description="Задать вопрос"),
            types.BotCommand(command="lawinfo", description="Права человека"),
            types.BotCommand(command="help", description="Помощь по боту"),
        ]
    elif is_lawyer:
        commands = [
            types.BotCommand(command="start", description="Запуск бота"),
            types.BotCommand(command="takequestion", description="Получить вопрос"),
            types.BotCommand(command="lawinfo", description="Права человека"),
            types.BotCommand(command="help", description="Помощь по боту"),
        ]
    else:
        commands = [
            types.BotCommand(command="start", description="Запуск бота"),
            types.BotCommand(command="registr", description="Регистрация"),
            types.BotCommand(command="lawinfo", description="Права человека"),
            types.BotCommand(command="help", description="Помощь по боту"),
            types.BotCommand(command="whyinfo", description="Зачем нужны данные")
        ]

    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user_id))
    
@dp.message(Command("start"))
async def start(message: types.Message, bot: Bot):
    await message.answer(
    "Здравствуйте!\n"
    "Это бот <b><i>Юридическая помощь</i></b>. Задайте свой вопрос — мы поможем или передадим его юристу.",
    parse_mode=ParseMode.HTML
)
    await set_personal_commands(bot, message.from_user.id)

@dp.message(Command('help'))
async def help_message(message: types.Message):
    async with aiosqlite.connect("telegram_data_base.db") as db:
        user = await db.execute("SELECT id FROM users WHERE id = ?", (message.user_id,))
        is_user = await user.fetchone()
        lawyer = await db.execute("SELECT id FROM lawyers WHERE id = ?", (message.user_id,))
        is_lawyer = await lawyer.fetchone()

    if is_user:
        text = """"📌 Команды для пользователя:\n\n"
                    "/start — запуск бота\n"
                    "/ask — задать юридический вопрос\n"
                    "/lawinfo — статьи о правах человека\n"
                    "/help — показать это меню помощи\n\n"
                    Если у вас возникли проблемы с использованием бота, просто напишите ваш вопрос — мы поможем!
                    """
        await message.answer(text)
    elif is_lawyer:
        text = """""📌 Команды для юриста:\n\n"
                    "/start — запуск бота\n"
                    "/takequestion — получить новый вопрос от пользователя\n"
                    "/lawinfo — статьи о правах человека\n"
                    "/help — показать это меню помощи\n\n"
                    Если у вас возникли проблемы с использованием бота, просто напишите ваш вопрос — мы поможем!
                    """
        await message.answer(text)
    else:
        text = """"📌 Команды:\n\n"
                    "/start — запуск бота\n"
                    "/registr — регистрация пользователя или юриста\n"
                    "/lawinfo — статьи о правах человека\n"
                    "/help — показать это меню помощи\n"
                    "/whyinfo — зачем нужны ваши данные"\n\n
                    Если у вас возникли проблемы с использованием бота, просто напишите ваш вопрос — мы поможем!
                    """
        await message.answer(text)

# =========================  ПОЛЬЗОВАТЕЛЬ  =========================== #
@dp.message(UserRegistrationStates.second_name)
async def get_second_name(message: types.Message, state: FSMContext):
    await state.update_data(second_name=message.text)
    await message.answer("Введите ваше имя:")
    await state.set_state(UserRegistrationStates.first_name)

@dp.message(UserRegistrationStates.first_name)
async def get_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите ваше отчество:")
    await state.set_state(UserRegistrationStates.patronymic)

@dp.message(UserRegistrationStates.patronymic)
async def get_patronymic(message: types.Message, state: FSMContext):
    await state.update_data(patronymic=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(UserRegistrationStates.phone)

@dp.message(UserRegistrationStates.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите email:")
    await state.set_state(UserRegistrationStates.email)

@dp.message(UserRegistrationStates.email)
async def get_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    data = await state.get_data()

    telegram_id = message.from_user.id
    date = datetime.date.today()

    async with aiosqlite.connect("telegram_data_base.db") as db:
        cursor = await db.execute("SELECT id FROM users WHERE id = ?", (telegram_id,))
        if await cursor.fetchone() is None:
          await db.execute("INSERT INTO users (id, username, question_ask, created_at) VALUES (?, ?, ?, ?)", 
                     (telegram_id, message.from_user.username, False, date))
          await db.execute("""
            INSERT INTO user_profile (user_id, first_name, second_name, patronymic, phone, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            telegram_id,
            data["first_name"],
            data["second_name"],
            data["patronymic"],
            data["phone"],
            data["email"]
        ))
        await db.commit()

    await message.answer("Регистрация пользователя завершена успешно. Ваши данные будут защищены, не волнуйтесь!\n\nОтправьте команду \start и расширьте возможности!")
    await message.answer("Введите ваш вопрос!")  
    await state.set_state(YourStates.waiting_for_question)   
             
    await state.clear()
      
@dp.callback_query(F.data == 'user_register')
async def question_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer("Регистрация пользователя.")
    await bot.send_message(chat_id=callback.message.chat.id, text="Введите вашу фамилию:")
    await state.set_state(UserRegistrationStates.second_name)

# =========================  ЮРИСТ  =========================== #
@dp.message(LawyerRegistrationStates.second_name)
async def lawyer_second_name(message: types.Message, state: FSMContext):
    await state.update_data(second_name=message.text)
    await message.answer("Введите ваше имя:")
    await state.set_state(LawyerRegistrationStates.first_name)

@dp.message(LawyerRegistrationStates.first_name)
async def lawyer_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите ваше отчество:")
    await state.set_state(LawyerRegistrationStates.patronymic)

@dp.message(LawyerRegistrationStates.patronymic)
async def lawyer_patronymic(message: types.Message, state: FSMContext):
    await state.update_data(patronymic=message.text)
    await message.answer("Укажите вашу специализацию:")
    await state.set_state(LawyerRegistrationStates.specialization)

@dp.message(LawyerRegistrationStates.specialization)
async def lawyer_specialization(message: types.Message, state: FSMContext):
    await state.update_data(specialization=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(LawyerRegistrationStates.phone)

@dp.message(LawyerRegistrationStates.phone)
async def lawyer_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите email:")
    await state.set_state(LawyerRegistrationStates.email)

@dp.message(LawyerRegistrationStates.email)
async def lawyer_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    data = await state.get_data()
    lawyer_id = message.from_user.id
    date = datetime.date.today()

    async with aiosqlite.connect("telegram_data_base.db") as db:
        cursor = await db.execute("SELECT id FROM lawyers WHERE id = ?", (lawyer_id,))
        if await cursor.fetchone() is None:
            await db.execute("""
                INSERT INTO lawyers (id, username, active, available_for_new_questions, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (lawyer_id, message.from_user.username, True, True, date))

            await db.execute("""
                INSERT INTO lawyer_profile (lawyer_id, first_name, second_name, patronymic, specialization, phone, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lawyer_id,
                data["first_name"],
                data["second_name"],
                data["patronymic"],
                data["specialization"],
                data["phone"],
                data["email"]
            ))
            await db.commit()

    await message.answer("Регистрация юриста завершена успешно. Ваши данные будут защищены, не волнуйтесь!\n\nОтправьте команду \start и расширьте возможности!")
    await state.clear()

@dp.callback_query(F.data == 'lawyer_register')
async def question_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer("Регистрация юриста.")
    await bot.send_message(chat_id=callback.message.chat.id, text="Введите вашу фамилию:")
    await state.set_state(LawyerRegistrationStates.second_name)

@dp.message(Command('registr'))
async def ask_command(message: types.Message, state: FSMContext):
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT * FROM users WHERE id = ?', (message.from_user.id,))
        result = await cursor.fetchone()

        if result is None:
            await message.answer("Так как вы еще не прошли регистрацию, сейчас самое время!\n", reply_markup=user_lawyer)
    
@dp.message(Command('whyinfo'))
async def whyinfo_command(message: types.Message):
    await message.answer(
        "Ваши данные нужны для:\n"
        "• идентификации;\n"
        "• правильного подбора юриста;\n"
        "• персональной консультации.\n\n"
        "Мы храним их безопасно и не передаём третьим лицам."
    )


@dp.message(Command('lawinfo'))
async def lawinfo(message:types.Message):
    await message.answer(text="Перейдя по следующей ссылке, вы получите полезные статьи о правах человека в обновлённой Конституции Республики Узбекистан:\n\n"
             "🔗 https://gk-usbekistan.de/ru/2023/11/13/права-человека-в-обновленной-констит/")
    
@dp.message(Command('ask'))
async def ask_command(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT id FROM users WHERE id = ?', (telegram_id,))
        result = await cursor.fetchone()

    if result:
        await message.answer("Введите ваш юридический вопрос:")
        await state.set_state(YourStates.waiting_for_question)
    else:
        await message.answer("Вы не зарегистрированы. Пожалуйста, сначала зарегистрируйтесь через /registr.")

@dp.message(YourStates.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    question_text = message.text
    
    async with aiosqlite.connect("telegram_data_base.db") as db:
        # Сохраняем вопрос в БД
        await db.execute(
            "INSERT INTO questions (user_id, question_text, status) VALUES (?, ?, ?)",
            (user_id, question_text, 'ожидает')
        )
        await db.commit()
        
        # Ищем свободного юриста
        cursor = await db.execute("""
            SELECT id FROM lawyers 
            WHERE available_for_new_questions = TRUE AND active = TRUE 
            LIMIT 1
        """)
        lawyer = await cursor.fetchone()
        
        if lawyer:
            lawyer_id = lawyer[0]
            # Отправляем уведомление юристу
            await bot.send_message(
                lawyer_id,
                "🔔 Появился новый юридический вопрос! \nИспользуйте команду /takequestion, чтобы взять его в работу."
            )
            await message.answer("Спасибо! Ваш вопрос принят и в ближайшее время будет передан свободному юристу.")
        else:
            await message.answer("Спасибо! Ваш вопрос принят и поставлен в очередь. Как только юрист освободится, он займется вашим вопросом.")
            
    await state.clear()

@dp.message(Command("takequestion"))
async def take_question(message: types.Message, state: FSMContext): # Добавили state: FSMContext
    lawyer_id = message.from_user.id

    async with aiosqlite.connect("telegram_data_base.db") as db:
        # Проверим, что юрист зарегистрирован
        cursor = await db.execute("SELECT id FROM lawyers WHERE id = ?", (lawyer_id,))
        if not await cursor.fetchone():
            await message.answer("Вы не зарегистрированы как юрист.")
            return

        # Найдём первый ожидающий вопрос
        cursor = await db.execute("""
            SELECT id, user_id, question_text FROM questions 
            WHERE status IN ('новый','ожидает') 
            ORDER BY created_at 
            LIMIT 1
        """)
        question = await cursor.fetchone()

        if not question:
            await message.answer("В данный момент нет вопросов в ожидании.")
            return

        question_id, user_id, question_text = question

        # Назначим вопрос юристу и обновим его статус
        await db.execute("""
            UPDATE questions 
            SET status = 'в работе', assigned_lawyer_id = ? 
            WHERE id = ?
        """, (lawyer_id, question_id))

        # Пометим юриста как занятого
        await db.execute("""
            UPDATE lawyers 
            SET available_for_new_questions = FALSE 
            WHERE id = ?
        """, (lawyer_id,))
        await db.commit()

        await message.answer(f"Вам назначен вопрос #{question_id} от пользователя.\n\n"
                             f"❓ **Текст вопроса:**\n{question_text}\n\n"
                             f"Пожалуйста, напишите ваш ответ следующим сообщением.", parse_mode=ParseMode.MARKDOWN)
        await state.update_data(question_id=question_id, user_id=user_id)
        await state.set_state(AnsweringStates.waiting_for_answer)

@dp.message(AnsweringStates.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext):
    lawyer_id = message.from_user.id
    answer_text = message.text
    
    data = await state.get_data()
    question_id = data.get("question_id")
    user_id = data.get("user_id")

    if not all([question_id, user_id]):
        await message.answer("Произошла ошибка. Не удалось определить, на какой вопрос вы отвечаете. Попробуйте снова.")
        await state.clear()
        return

    async with aiosqlite.connect("telegram_data_base.db") as db:
        # Сохраняем ответ в БД
        await db.execute(
            """INSERT INTO answers (question_id, lawyer_id, user_id, question_text) 
               VALUES (?, ?, ?, ?)""",
            (question_id, lawyer_id, user_id, answer_text)
        )
        
        # Обновляем статус вопроса на "завершён"
        await db.execute("UPDATE questions SET status = 'завершён' WHERE id = ?", (question_id,))
        
        # Освобождаем юриста для новых вопросов
        await db.execute("UPDATE lawyers SET available_for_new_questions = TRUE WHERE id = ?", (lawyer_id,))
        
        await db.commit()

    # Отправляем ответ пользователю
    try:
        await bot.send_message(
            user_id,
            f"⚖️ **Получен ответ от юриста на ваш вопрос #{question_id}:**\n\n{answer_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        await message.answer("✅ Ваш ответ успешно отправлен пользователю!")
    except Exception as e:
        logging.error(f"Не удалось отправить ответ пользователю {user_id}: {e}")
        await message.answer("❗️ Не удалось доставить ответ пользователю. Возможно, он заблокировал бота. Ваш ответ сохранен.")

    await state.clear()


# Запуск процесса поллинга новых апдейтов
async def main():
    async with aiosqlite.connect('telegram_data_base.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username VARCHAR(100),
                question_ask BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id BIGINT PRIMARY KEY,
                first_name VARCHAR(15),
                second_name VARCHAR(15),
                patronymic VARCHAR(15),
                phone VARCHAR(20),
                email VARCHAR(100),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
           CREATE TABLE IF NOT EXISTS lawyers (
                id BIGINT PRIMARY KEY,
                username VARCHAR(100),
                active BOOLEAN DEFAULT TRUE,
                available_for_new_questions BOOLEAN DEFAULT TRUE, -- чтобы знать, свободен ли юрист
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lawyer_profile (
                lawyer_id BIGINT PRIMARY KEY,
                first_name VARCHAR(15),
                second_name VARCHAR(15),
                patronymic VARCHAR(15),
                specialization VARCHAR(255),
                phone VARCHAR(20),
                email VARCHAR(100),
                FOREIGN KEY (lawyer_id) REFERENCES lawyers(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                question_text TEXT NOT NULL,
                status TEXT DEFAULT 'новый', -- например: новый, в работе, завершён
                assigned_lawyer_id BIGINT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_lawyer_id) REFERENCES lawyers(id) ON DELETE SET NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                lawyer_id BIGINT,
                user_id BIGINT,
                valuation_service INT NOT NULL DEFAULT 0,
                question_text TEXT NOT NULL,
                start_chat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_chat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                link_document VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (lawyer_id) REFERENCES lawyers(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
        """)
        
        await db.commit()

    # dp.message.register(process_question, StateFilter(YourStates.waiting_for_question))
    await dp.start_polling(bot)
        
    
if __name__ == "__main__":
    asyncio.run(main())
