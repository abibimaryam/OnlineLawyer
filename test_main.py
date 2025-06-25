import pytest
from unittest.mock import AsyncMock, patch
from main import send_pending_answers

@pytest.mark.asyncio
@patch("main.Bot")
@patch("aiosqlite.connect")
async def test_send_pending_answers_sends_message(mock_connect, mock_bot_class):
    mock_db = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchall.return_value = [(1, 123456, 42, "Ответ пользователя")]
    mock_db.execute.return_value = mock_cursor
    mock_connect.return_value.__aenter__.return_value = mock_db

    mock_bot = AsyncMock()
    mock_bot_class.return_value = mock_bot

    task = asyncio.create_task(send_pending_answers())
    await asyncio.sleep(0.1)
    task.cancel()

    mock_bot.send_message.assert_called_once()
    
