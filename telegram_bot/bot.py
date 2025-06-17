import os
import asyncio
import logging
from telegram.ext import Application
from telegram_bot.law_handlers import LawHandlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OnlineLawyer.settings")
    import django
    django.setup()


def run_bot():
    setup_django()
    from telegram_bot.help import HelpHandler
    from telegram_bot.auth.handlers import AuthHandlers
    from telegram_bot.requests.handlers import RequestHandlers
    from telegram_bot.session.handlers import SessionHandler

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    from django.conf import settings
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    handlers = [
        *HelpHandler().get_handler(),
        *AuthHandlers().get_handlers(),
        *RequestHandlers().get_handlers(),
        *LawHandlers().get_handlers(),
        *SessionHandler().get_handlers(),
    ]
    for handler in handlers: application.add_handler(handler)
    logger.info("The bot has been launched...")
    application.run_polling()