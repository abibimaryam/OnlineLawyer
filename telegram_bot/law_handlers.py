import aiosqlite
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

QUESTION = 1  

class LawHandlers:
   
    async def start_ask_lawyer(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text(
            "✍️ Напишите ваш вопрос юристу одним сообщением.\n"
            "Если передумаете — /cancel"
        )
        return QUESTION

  
    async def receive_question(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
      
        context.args = [update.message.text.strip()]
        await self._legacy_ask_lawyer(update, context)
        return ConversationHandler.END

   
    async def cancel(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text("Действие отменено.")
        return ConversationHandler.END

 
    async def _legacy_ask_lawyer(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not context.args:
            await update.message.reply_text(
                "Пожалуйста, используйте: /ask_lawyer ваш вопрос"
            )
            return

        user_id = update.effective_user.id
        question_text = " ".join(context.args)

        async with aiosqlite.connect("telegram_data_base.db") as db:
            await db.execute(
                "INSERT INTO questions (user_id, question_text, status) VALUES (?, ?, ?)",
                (user_id, question_text, "новый"),
            )
            await db.commit()

            cursor = await db.execute(
                "SELECT id FROM lawyers WHERE available_for_new_questions = 1 AND active = 1 LIMIT 1"
            )
            row = await cursor.fetchone()

            if row:
                lawyer_id = row[0]  
                await update.message.reply_text("Спасибо! Ваш вопрос отправлен юристу.")
            else:
                await update.message.reply_text(
                    "Все юристы сейчас заняты. Ваш вопрос поставлен в очередь."
                )

  
    def get_handlers(self):
        return [
            ConversationHandler(
                entry_points=[CommandHandler("ask_lawyer", self.start_ask_lawyer)],
                states={
                    QUESTION: [
                        MessageHandler(
                            filters.TEXT & ~filters.COMMAND, self.receive_question
                        )
                    ]
                },
                fallbacks=[CommandHandler("cancel", self.cancel)],
            )
        ]
