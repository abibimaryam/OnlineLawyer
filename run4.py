import asyncio
import logging
import aiosqlite
import datetime
from config import TOKEN 
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

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=TOKEN)
# Диспетчер
dp = Dispatcher(storage=MemoryStorage())

# Данные юриста 
class LawyerRegistrationStates(StatesGroup):
    login = State()
    email = State()
    password = State()

class LawyerLoginStates(StatesGroup):
    login = State()
    email = State()
    password = State()
    
# Состояние для юриста, который отвечает на вопрос
class AnsweringStates(StatesGroup):
    waiting_for_answer = State()
    

# Команды
async def set_personal_commands(bot: Bot, user_id: int, state: FSMContext):
    async with aiosqlite.connect("telegram_data_base.db") as db:
        lawyer = await db.execute("SELECT id FROM lawyers WHERE id = ?", (user_id,))
        is_lawyer = await lawyer.fetchone()

    if is_lawyer:
        commands = [
            types.BotCommand(command="start", description="Запуск бота"),
            types.BotCommand(command="take_question", description="Получить вопрос"),
            types.BotCommand(command="lawinfo", description="Права человека"),
            types.BotCommand(command="help", description="Помощь по боту"),
        ]
        await bot.send_message(user_id, "🕐 Мы вам сообщим, как только появится новый вопрос!")  
    else:
        commands = [
            types.BotCommand(command="start", description="Запуск бота"),
            types.BotCommand(command="register", description="Регистрация"),
            types.BotCommand(command="lawinfo", description="Права человека"),
            types.BotCommand(command="help", description="Помощь по боту"),
        ]
        await bot.send_message(user_id, "👤Пройдите регистрацию по команде /register")  
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user_id))

@dp.message(Command('help'))
async def help_message(message: types.Message, state: FSMContext):
    async with aiosqlite.connect("telegram_data_base.db") as db:
        lawyer = await db.execute("SELECT id FROM lawyers WHERE id = ?", (message.user_id,))
        is_lawyer = await lawyer.fetchone()
 
    if is_lawyer:
        text = """""📌 Команды для юриста:\n\n"
                    "/start — запуск бота\n"
                    "/take_question — получить новый вопрос от пользователя\n"
                    "/lawinfo — статьи о правах человека\n"
                    "/help — показать это меню помощи\n\n"
                    Если у вас возникли проблемы с использованием бота, просто напишите ваш вопрос — мы поможем!
                    """
        await message.answer(text)
    else:
        text = """"📌 Команды:\n\n"
                    "/start — запуск бота\n"
                    "/register — регистрация пользователя или юриста\n"
                    "/lawinfo — статьи о правах человека\n"
                    "/help — показать это меню помощи\n\n"
                    Если у вас возникли проблемы с использованием бота, просто напишите ваш вопрос — мы поможем!
                    """
        await message.answer(text)

@dp.message(Command("start"))
async def start(message: types.Message, bot: Bot):
    await message.answer(
    "Здравствуйте!\n"
    "Вы обратились в бот <b><i>«Вопросы по юриспруденции»</i></b>.\n\n"
    "Данный сервис создан для того, чтобы квалифицированные юристы могли получать обращения от пользователей, содержащие правовые вопросы, и оказывать информационную поддержку в рамках действующего законодательства.\n\n"
    "Пользователи могут изложить суть своей ситуации, а юрист, ознакомившись с деталями, предоставит возможные пути решения, ссылки на нормы права или рекомендации по дальнейшим действиям.\n\n",
    parse_mode=ParseMode.HTML
)
    
    await message.answer("Выберите команду", 
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Войти', callback_data='login'), InlineKeyboardButton(text='Регистрация', callback_data='register')]]))
    
    
@dp.message(Command("register"))
async def question_callback(state: FSMContext, bot: Bot, message: types.Message):
    # Проверка есть ли юрист в системе
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT * FROM lawyers WHERE id = ?', (message.from_user.id,))
        result = await cursor.fetchone()

        if result is None:
            await message.answer("Регистрация юриста.")
            await bot.send_message(chat_id=message.chat.id, text="Введите вашу login:")
            await state.set_state(LawyerRegistrationStates.login)
        else:
            await message.answer("Так как вы уже прошли регистрацию, рекомендуется войти в аккаунт!\n", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Войти', callback_data='login')]]))
            
            # await message.answer("Так как вы еще не прошли регистрацию, сейчас самое время!\n", reply_markup=lawyer)



@dp.callback_query(F.data == 'register')
async def question_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT * FROM lawyers WHERE id = ?', (user_id,))
        result = await cursor.fetchone()

        if result is None:
            await callback.answer("Регистрация юриста.")
            await bot.send_message(chat_id=callback.message.chat.id, text="Введите вашу login:")
            await state.set_state(LawyerRegistrationStates.login)
        else:
            await bot.send_message(chat_id=callback.message.chat.id, 
                                   text="Так как вы уже прошли регистрацию, рекомендуется войти в аккаунт!",
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text='Войти', callback_data='login')]
                                   ]))
            # await message.answer("Так как вы еще не прошли регистрацию, сейчас самое время!\n", reply_markup=lawyer)

@dp.message(Command('lawinfo'))
async def lawinfo(message:types.Message):
    await message.answer(text="Перейдя по следующей ссылке, вы получите полезные статьи о правах человека в обновлённой Конституции Республики Узбекистан:\n\n"
             "🔗 https://gk-usbekistan.de/ru/2023/11/13/права-человека-в-обновленной-констит/")
    
    
# @dp.message(YourStates.waiting_for_question)
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
                "🔔 Появился новый юридический вопрос! \nИспользуйте команду /take_question, чтобы взять его в работу."
            )
            await message.answer("Спасибо! Ваш вопрос принят и в ближайшее время будет передан свободному юристу.")
        else:
            await message.answer("Спасибо! Ваш вопрос принят и поставлен в очередь. Как только юрист освободится, он займется вашим вопросом.")
            
    await state.clear()
    
    
#!================ Войти =========================== #
@dp.callback_query(F.data == 'log_out')
async def lawyer_logout(callback: CallbackQuery):
    await callback.answer()
    lawyer_id = callback.from_user.id

    async with aiosqlite.connect('telegram_data_base.db') as db:
        await db.execute("""
            UPDATE lawyer_profile 
            SET log = FALSE
            WHERE lawyer_id = ?
        """, (lawyer_id,))
        await db.commit()

    await callback.message.answer("Успешный выход!")
    await callback.message.answer(
        "Выберите команду", 
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Войти', callback_data='login'),
                    InlineKeyboardButton(text='Регистрация', callback_data='register')
                ]
            ]
        )
    )

@dp.message(Command("take_question"))
@dp.message(AnsweringStates.waiting_for_answer)
async def handle_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_id = data.get("question_id")
    user_id = data.get("user_id")
    answer_text = message.text

    async with aiosqlite.connect("telegram_data_base.db") as db:
        await db.execute("""
            UPDATE questions 
            SET status = 'отвечен', answer_text = ?, answered_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (answer_text, question_id))

        await db.execute("""
            UPDATE lawyers 
            SET available_for_new_questions = TRUE 
            WHERE id = ?
        """, (message.from_user.id,))
        await db.commit()

    await message.answer("Ваш ответ отправлен пользователю. Спасибо!")
    await state.clear()

    # Уведомим пользователя (если нужно, добавь бота в users DB и найди chat_id)
    # await bot.send_message(chat_id=user_id, text=f"Вам ответили на вопрос #{question_id}:\n\n{answer_text}")

@dp.callback_query(F.data == 'take_question')
async def take_question(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    lawyer_id = callback.from_user.id

    async with aiosqlite.connect("telegram_data_base.db") as db:
        # Проверим, что юрист зарегистрирован
        cursor = await db.execute("SELECT id FROM lawyers WHERE id = ?", (lawyer_id,))
        if not await cursor.fetchone():
            await callback.message.answer("Вы не зарегистрированы!\nПройдите регистрацию по команде /register")
            return

        # Найдём первый ожидающий вопрос
        cursor = await db.execute("""
            SELECT id, user_id, question_text FROM questions 
            WHERE status = 'ожидает' 
            ORDER BY created_at 
            LIMIT 1
        """)
        question = await cursor.fetchone()

        if not question:
            await callback.message.answer("В данный момент нет вопросов в ожидании.")
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

        await callback.message.answer(
            f"Вам назначен вопрос #{question_id} от пользователя.\n\n"
            f"❓ **Текст вопроса:**\n{question_text}\n\n"
            f"Пожалуйста, напишите ваш ответ следующим сообщением.",
            parse_mode=ParseMode.MARKDOWN
        )


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

# ==== Проверка пароля
@dp.message(LawyerLoginStates.password)
@dp.message(LawyerLoginStates.password)
async def lawyer_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute(
            'SELECT * FROM lawyer_profile WHERE lawyer_id = ? AND password = ?',
            (message.from_user.id, message.text)
        )
        result = await cursor.fetchone()
        if result is None:
            await message.answer("Неправильный пароль!\nПопробуйте еще раз!")
            await message.answer("Введите пароль:")
            await state.set_state(LawyerLoginStates.password)
        else:
            await db.execute(
                "UPDATE lawyer_profile SET log = TRUE WHERE lawyer_id = ?",
                (message.from_user.id,)  # <- правильно!
            )
            await db.commit()  # <- обязательно сохранить!
            
            await message.answer(
                "Успешный вход!\n\nОтправьте команду \\start и расширьте возможности!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text='Вопрос', callback_data='take_question'),
                            InlineKeyboardButton(text='Выйти', callback_data='log_out')
                        ]
                    ]
                )
            )


# ==== Проверка email
@dp.message(LawyerLoginStates.email)
async def lawyer_email(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect('telegram_data_base.db') as db:
        db.row_factory = aiosqlite.Row  # это позволит обращаться по ключам
        cursor = await db.execute('SELECT * FROM lawyer_profile WHERE lawyer_id = ? AND email = ? AND login = ?', (message.from_user.id, message.text,  data["login"],))
        result = await cursor.fetchone()
        
        if result is None:
            await message.answer("Неправильный email!\n Попробуйте еще раз!")
            await message.answer("Введите email:")
            await state.set_state(LawyerLoginStates.email)
        else:
            if result and result["log"]:
                 await message.answer("Вы уже вошли в аккаунт.", 
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Вопрос', callback_data='take_question'), InlineKeyboardButton(text='Выйти', callback_data='log_out')]]))
            else:
                await state.update_data(email=message.text)
                await message.answer("Введите пароль:")
                await state.set_state(LawyerLoginStates.password)

# ==== Проверка login
@dp.message(LawyerLoginStates.login)
async def lawyer_login(message: types.Message, state: FSMContext):
    
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT lawyer_id, login FROM lawyer_profile WHERE lawyer_id = ? AND login = ?', (message.from_user.id, message.text,))
        result = await cursor.fetchone()
        if result is None:
            await message.answer("Неправильный login!\n Попробуйте еще раз!")
            await message.answer("Введите login:")
            await state.set_state(LawyerLoginStates.login)
        else:
            await state.update_data(login=message.text)
            await message.answer("Введите email:")
            await state.set_state(LawyerLoginStates.email)
    
@dp.callback_query(F.data == 'login')
async def lawyer_log_in(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите login:")
    await state.set_state(LawyerLoginStates.login)
#?====================== Регистрация  =========================== #

@dp.message(LawyerRegistrationStates.password)
async def lawyer_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
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
                INSERT INTO lawyer_profile (lawyer_id, log, login, email, password)
                VALUES (?, ?, ?, ?, ?)
            """, (
                lawyer_id,
                False,
                data["login"],
                data["email"],
                data["password"],
            ))
            await db.commit()

    await message.answer("Регистрация юриста завершена успешно. Ваши данные будут защищены, не волнуйтесь!\n\n", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Войти', callback_data='login')]]))
    await state.clear()
  
  
@dp.message(LawyerRegistrationStates.email)
async def lawyer_email(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT lawyer_id, email, login, log FROM lawyer_profile WHERE lawyer_id = ? AND email = ? AND login = ?', (message.from_user.id, message.text,  data["login"],))
        result = await cursor.fetchone()
        if result is None:# Регистрации не было
                    await state.update_data(email=message.text)
                    await message.answer("Введите пароль:")
                    await state.set_state(LawyerRegistrationStates.password)
        else:
            await message.answer("Вы уже прошли регистрацию, войдите в профиль!\n",
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Войти', callback_data='login')]]))
      
    
@dp.message(LawyerRegistrationStates.login)
async def lawyer_login(message: types.Message, state: FSMContext):
    
    async with aiosqlite.connect('telegram_data_base.db') as db:
        cursor = await db.execute('SELECT lawyer_id, login FROM lawyer_profile WHERE lawyer_id = ? AND login = ?', (message.from_user.id, message.text,))
        result = await cursor.fetchone()
        if result is None:# Регистрации не было
                await state.update_data(login=message.text)
                await message.answer("Введите email:")
                await state.set_state(LawyerRegistrationStates.email)
        else:
            await message.answer("Вы уже прошли регистрацию, войдите в профиль!\n",
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Войти', callback_data='login')]]))
    




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
                log BOOLEAN DEFAULT FALSE,
                login VARCHAR(15),
                email VARCHAR(100),
                password VARCHAR(100),
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