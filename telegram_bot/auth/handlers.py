from asgiref.sync import sync_to_async
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
from telegram import Update
from .service import AuthService
from telegram_bot.keyboards import get_main_keyboard

USERNAME, PASSWORD = range(2)
USERNAME_REG, EMAIL_REG, PASSWORD_REG = range(3, 6)


class AuthHandlers:
    def __init__(self):
        self.service = AuthService()

    async def start(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        user = await self.service.get_user(update.effective_user.id)
        if user:
            text = (f"Welcome back, {user.username}.\n"
                    f"Your account has been successfully linked.\n\n"
                    f"Username: {user.username}\nEmail: {user.email}\n\n"
                    f"To switch accounts, use the /login command.")
        else:
            text = "Welcome. To continue, please log in using the /login command."
        await update.message.reply_text(text, reply_markup=get_main_keyboard())

    async def register(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("Enter a username for registration:")
        return USERNAME_REG

    async def handle_username_reg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        username = update.message.text.strip()
        if len(username) < 4:
            await update.message.reply_text("Username too short (min 4 characters). Try again:")
            return USERNAME_REG

        exists = await sync_to_async(self.service.User.objects.filter(username=username).exists)()
        if exists:
            await update.message.reply_text("Username already exists. Please choose another one:")
            return USERNAME_REG

        context.user_data["username"] = username
        await update.message.reply_text("Enter your email:")
        return EMAIL_REG

    async def handle_email_reg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        email = update.message.text.strip()
        if '@' not in email or '.' not in email.split('@')[-1]:
            await update.message.reply_text("Invalid email format. Please enter a valid email:")
            return EMAIL_REG

        exists = await sync_to_async(self.service.User.objects.filter(email=email).exists)()
        if exists:
            await update.message.reply_text("Email already in use. Please enter another email:")
            return EMAIL_REG

        context.user_data["email"] = email
        await update.message.reply_text("Enter a password (min 8 characters):")
        return PASSWORD_REG

    async def handle_password_reg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        password = update.message.text.strip()
        if len(password) < 8:
            await update.message.reply_text("Password too short (min 8 characters). Try again:")
            return PASSWORD_REG

        validation_errors = await sync_to_async(validate_password)(password, None)
        if validation_errors:
            await update.message.reply_text(f"Password invalid: {validation_errors}\nTry again:")
            return PASSWORD_REG

        user = await sync_to_async(self.service.User.objects.create_user)(
            username=context.user_data["username"],
            email=context.user_data["email"],
            password=password,
            is_active=True
        )

        default_group, _ = await sync_to_async(Group.objects.get_or_create)(name='Users')
        await sync_to_async(user.groups.add)(default_group)

        await self.service.update_telegram_data(
            user,
            update.effective_user.id,
            update.effective_user.username
        )

        await update.message.reply_text(
            f"Registration successful! Welcome, {user.username}!",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("Enter the username or email:")
        return USERNAME

    async def handle_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data["identifier"] = update.message.text.strip()
        await update.message.reply_text("Enter the password:")
        return PASSWORD

    async def handle_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = await self.service.authenticate(
            context.user_data["identifier"],
            update.message.text
        )
        if not user:
            await update.message.reply_text("Authentication failed. Wrong credentials.")
            return ConversationHandler.END

        await self.service.update_telegram_data(
            user,
            update.effective_user.id,
            update.effective_user.username
        )
        await update.message.reply_text(f"Successful login, {user.username}!")
        return ConversationHandler.END

    async def logout(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        await self.service.update_telegram_data(None, update.effective_user.id, None)
        await update.message.reply_text("Session has been closed")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text("Authentication has been canceled")
        return ConversationHandler.END

    def get_handlers(self) -> list:
        return [
            CommandHandler("start", self.start),
            CommandHandler("logout", self.logout),
            ConversationHandler(
                entry_points=[CommandHandler("login", self.login)],
                states={
                    USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_username)],
                    PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_password)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel)],
            ),
            ConversationHandler(
                entry_points=[CommandHandler("register", self.register)],
                states={
                    USERNAME_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_username_reg)],
                    EMAIL_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_email_reg)],
                    PASSWORD_REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_password_reg)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel)],
            )
        ]