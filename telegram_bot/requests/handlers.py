from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram_bot.auth.decorators import auth_required


class RequestHandlers:
    @auth_required
    async def request_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not context.args:
            await update.message.reply_text(
                "Please, enter your request text: /request your_text"
            )
            return

        processing_message = await update.message.reply_text("Processing request......")

        try:
            user_request_text = " ".join(context.args)
            result = f"Your request: {user_request_text}\nAnswer: Sample answer."
            await processing_message.delete()
            await update.message.reply_text(result)
        except Exception as e:
            await processing_message.edit_text(f"An error has occurred: {e}")

    def get_handlers(self) -> list:
        return [CommandHandler("request", self.request_command)]
