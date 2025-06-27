import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import agents

pytestmark = pytest.mark.asyncio

@patch('agents.AgentWorkflow')
async def test_analyze(mock_agent_workflow):
    mock_instance = AsyncMock()
    mock_instance.run.return_value = "Краткое содержание: Юридическая проблема"
    mock_agent_workflow.from_tools_or_functions.return_value = mock_instance

    conv = [{"role": "user", "content": "У меня проблема с договором"}]
    result = await agents.analyze(conv)

    assert any(keyword in result.lower() for keyword in ["краткое содержание", "резюме", "анализ"]), \
        f"Результат не содержит ожидаемых ключевых слов: {result}"

@patch('agents.init_query_engine')
@patch('agents.AgentWorkflow')
async def test_pass_a_verdict(mock_agent_workflow, mock_init_query_engine):
    mock_instance = AsyncMock()
    mock_instance.run.return_value = "Вердикт: договор считается недействительным"
    mock_agent_workflow.from_tools_or_functions.return_value = mock_instance

    mock_init_query_engine.return_value = "dummy_query_engine"

    summarize_conv = "История общения"
    result = await agents.pass_a_verdict(summarize_conv)

    assert any(keyword in result.lower() for keyword in ["вердикт", "заключение", "вывод"]), \
        f"Результат не содержит ожидаемых ключевых слов: {result}"

@patch('agents.AgentWorkflow')
async def test_risk_estimate_and_forecast(mock_agent_workflow):
    mock_instance = AsyncMock()
    mock_instance.run.return_value = "Риски: средние, прогноз: неблагоприятный"
    mock_agent_workflow.from_tools_or_functions.return_value = mock_instance

    summarize_conv = "История"
    verdict = "Вердикт"
    result = await agents.risk_estimate_and_forecast(summarize_conv, verdict)

    assert any(keyword in result.lower() for keyword in ["риски", "прогноз", "оценка"]), \
        f"Результат не содержит ожидаемых ключевых слов: {result}"

@patch('agents.AgentWorkflow')
async def test_review_func_passed(mock_agent_workflow):
    mock_instance = AsyncMock()
    mock_instance.run.return_value = "[ПРОВЕРКА: ПРОЙДЕНА]\nЮридическая рецензия: всё корректно."
    mock_agent_workflow.from_tools_or_functions.return_value = mock_instance

    result, passed = await agents.review_func("вердикт", "риски")

    assert passed is True
    assert "пройдена" in result.lower()

async def test_conversation():
    user_input = "У меня проблема с жильём"
    result = await agents.conversation(user_input)

    assert isinstance(result, list)
    assert result[0]["role"] == "assistant"
    assert result[1]["content"] == user_input
