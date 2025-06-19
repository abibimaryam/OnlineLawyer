import sys
from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram_bot.auth.decorators import auth_required

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from agents import conversation, analyze, pass_a_verdict, risk_estimate_and_forecast, review_func


def split_message(text: str, max_length: int = 4096) -> list[str]:
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


class RequestHandlers:
    @auth_required
    async def request_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message:
            return

        if not context.args:
            await update.message.reply_text("Пожалуйста, введите текст запроса: /ask_AI ваш_текст")
            return

        user_request_text = " ".join(context.args)
        processing_message = await update.message.reply_text("Обработка запроса...")

        try:
            conv = await conversation(user_request_text)

            summarize_conv = await analyze(conv)

            attempt = 0
            max_attempts = 3
            passed = False
            verdict = ""
            risks = ""

            while not passed and attempt < max_attempts:
                attempt += 1
                verdict = await pass_a_verdict(summarize_conv)

                risks = await risk_estimate_and_forecast(summarize_conv, verdict)

                _, passed = await review_func(verdict, risks)

            response = (
                f"🔹 Ваш запрос: {user_request_text}\n\n"
                f"📄 Краткая выжимка:\n{summarize_conv}\n\n"
                f"⚖️ Юридический вердикт:\n{verdict}\n\n"
                f"⚠️ Оценка рисков:\n{risks}"
            )

            await processing_message.delete()

            for part in split_message(response):
                await update.message.reply_text(part)

        except Exception as e:
            await processing_message.edit_text(f"Ошибка при обработке: {e}")
            raise

    def get_handlers(self) -> list:
        return [CommandHandler("ask_AI", self.request_command)]