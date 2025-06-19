from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram_bot.keyboards import get_main_keyboard

class SessionHandler:
    async def restart_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
       
        await update.message.reply_text(
            "Session has been restarted.",
            reply_markup=get_main_keyboard()
        )

    def get_handlers(self) -> list:
        return [CommandHandler("restart_session", self.restart_session)]
