import json
from unittest.mock import patch, MagicMock
from app.core.analyzer import extract_json_from_text, analyze_extracted_data, normalize_legacy_braces
from app.core.schemas import LLMResponse


CUSTOM_PROMPT_WITH_JSON = """Извлеки данные из текста.
Текст документа:
{pdf_text}

Верни результат строго в формате JSON:
{
  "patient_info": {
    "name": "ФИО пациента",
    "birth_date": "дата рождения"
  },
  "diagnoses": []
}"""


def _mock_client(content: str):
    client = MagicMock()
    client.chat.return_value = LLMResponse(content=content, model="test", finish_reason="stop", truncated=False)
    return client


@patch("app.core.analyzer.get_prompt_extract")
@patch("app.core.analyzer.get_llm_client")
def test_extract_json_custom_prompt_with_single_braces(mock_get_client, mock_get_prompt):
    """Регрессия: кастомный промпт с обычными скобками в JSON-примере не должен падать (KeyError patient_info)."""
    mock_get_prompt.return_value = CUSTOM_PROMPT_WITH_JSON
    mock_get_client.return_value = _mock_client('{"patient_info": {"name": "Иванов"}}')

    result, error = extract_json_from_text("текст осмотра")

    assert error is None
    assert json.loads(result)["patient_info"]["name"] == "Иванов"

    sent_prompt = mock_get_client.return_value.chat.call_args.kwargs["user_message"]
    assert "текст осмотра" in sent_prompt
    assert "{pdf_text}" not in sent_prompt
    assert '"patient_info": {' in sent_prompt


@patch("app.core.analyzer.get_prompt_analyze")
@patch("app.core.analyzer.get_llm_client")
def test_analyze_custom_prompt_with_single_braces(mock_get_client, mock_get_prompt):
    mock_get_prompt.return_value = 'Проанализируй данные: {json_data}. Пример оценки: {"score": 10}'
    mock_get_client.return_value = _mock_client("Отчёт")

    result, error = analyze_extracted_data('{"a": 1}')

    assert error is None
    assert result == "Отчёт"
    sent_prompt = mock_get_client.return_value.chat.call_args.kwargs["user_message"]
    assert '{"a": 1}' in sent_prompt
    assert '{"score": 10}' in sent_prompt


def test_normalize_legacy_braces():
    legacy = 'JSON:\n{{\n  "patient_info": {{\n    "name": "ФИО"\n  }}\n}}\nТекст: {pdf_text}'
    normalized = normalize_legacy_braces(legacy)
    assert "{{" not in normalized
    assert '"patient_info": {' in normalized
    assert "{pdf_text}" in normalized
