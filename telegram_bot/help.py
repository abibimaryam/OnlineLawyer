from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram_bot.keyboards import get_main_keyboard


class HelpHandler:
    async def show_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        help_text = """
<b>Команды бота</b>

<b>/start</b> - Активация бота
<b>/help</b> - Все команды (это сообщение)
<b>/register</b> - Регистрация в системе
<b>/login</b> - Авторизация в системе
<b>/logout</b> - Выход из аккаунта
<b>/cancel</b> - Прервать текущее действие

<b>/request [запрос]</b> - Запрос агента
<b>/ask_lawyer [вопрос]</b> - Задать вопрос юристу
<b>/restart_session</b> - Перезапустить
        """
        await update.message.reply_text(
            help_text, parse_mode="HTML", reply_markup=get_main_keyboard()
        )

    def get_handler(self) -> list:
        return [CommandHandler("help", self.show_help)]
