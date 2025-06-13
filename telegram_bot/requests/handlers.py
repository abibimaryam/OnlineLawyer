from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
from telegram_bot.auth.decorators import auth_required


class RequestHandlers:
    @auth_required
    async def request_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Please, enter your request text: /request your_text")
            return
        await update.message.reply_text(f"Answer")

    def get_handlers(self) -> list:
        return [
            CommandHandler("request", self.request_command)
        ]