from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from typing import Callable
from .service import AuthService


def auth_required(handler: Callable) -> Callable:
    @wraps(handler)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        service = AuthService()
        if not (user := await service.get_user(update.message.from_user.id)):
            await update.message.reply_text("Требуется авторизация /login")
            return
        context.user_data["auth_user"] = user
        return await handler(self, update, context, *args, **kwargs)
    return wrapper