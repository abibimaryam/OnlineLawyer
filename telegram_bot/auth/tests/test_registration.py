from run2 import get_second_name
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from unittest.mock import AsyncMock

import pytest

@pytest.mark.asyncio
async def test_user_registration_step():
    state = AsyncMock()
    message = AsyncMock(spec=Message)
    message.text = "Иванов"
    message.answer = AsyncMock() # Explicitly mock answer as AsyncMock
    await get_second_name(message, state)

    state.update_data.assert_called_once_with(second_name="Иванов")
    state.set_state.assert_called_once()
    message.answer.assert_called_once()
