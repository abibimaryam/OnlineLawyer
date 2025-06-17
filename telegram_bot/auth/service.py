from typing import Optional, Any
from asgiref.sync import sync_to_async

class AuthService:

    def __init__(self):
        from django.contrib.auth import get_user_model, authenticate
        self.User = get_user_model()
        self._authenticate = authenticate

    async def get_user(self, telegram_id: int) -> Optional[Any]:
        return await sync_to_async(self.User.objects.filter(telegram_id=telegram_id).first)()

    async def authenticate(self, identifier: str, password: str) -> Optional[Any]:
        lookup = {'email' if '@' in identifier else 'username': identifier}
        user = await sync_to_async(self.User.objects.filter(**lookup).first)()
        auth_username = user.username if user else identifier
        return await sync_to_async(self._authenticate)(
            username=auth_username,
            password=password
        ) if user or '@' not in identifier else None

    async def update_telegram_data(
            self,
            user: Optional[Any],
            telegram_id: int,
            telegram_username: Optional[str]
    ) -> None:
        await sync_to_async(self.User.objects.filter(telegram_id=telegram_id).update)(
            telegram_id=None,
            telegram_username=None
        )
        if user:
            user.telegram_id = telegram_id
            user.telegram_username = telegram_username.lstrip('@') if telegram_username else None
            await sync_to_async(user.save)()

    async def user_exists(self, **kwargs) -> bool:
        return await sync_to_async(self.User.objects.filter(**kwargs).exists)()