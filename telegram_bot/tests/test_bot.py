import pytest
from run2 import set_personal_commands
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch("aiosqlite.connect")
async def test_set_personal_commands_for_user(mock_connect):
    user_id = 1111
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.side_effect = [(1,), None]  # юзер есть, юрист — нет
    mock_conn.execute.return_value = mock_cursor
    mock_connect.return_value.__aenter__.return_value = mock_conn

    bot = AsyncMock()
    await set_personal_commands(bot, user_id)

    bot.set_my_commands.assert_called()
