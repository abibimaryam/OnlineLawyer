from telegram import Update
from telegram.ext import ContextTypes

KNOWN_COMMANDS = {
    "start",
    "help",
    "login",
    "logout",
    "ask_lawyer",
    "ask_ai",
    "cancel",
    "register",
    "restart_session",
}


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cmd_full = update.message.text.split()[0]
    cmd = cmd_full.lstrip("/").split("@")[0].lower()

    if cmd in KNOWN_COMMANDS:
        return
    await update.message.reply_text(
        f"⚠️ Команда {cmd_full} не распознана.\n"
        "Список доступных команд смотрите в /help"
    )
