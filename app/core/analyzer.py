from typing import Optional
import logging
from app.core.llm_client import get_llm_client
from app.core.schemas import ExtractedData
from app.database.session import SessionLocal
from app.database import crud
import json

logger = logging.getLogger(__name__)


DEFAULT_PROMPT_EXTRACT = """Ты — медицинский аналитик. Извлеки структурированные данные из текста медицинской документации.

Текст документа:
{pdf_text}

Верни результат строго в формате JSON:
{{
  "patient_info": {{
    "name": "ФИО пациента",
    "birth_date": "дата рождения",
    "gender": "пол"
  }},
  "diagnoses": [
    {{
      "code": "код МКБ",
      "name": "название диагноза",
      "date": "дата постановки"
    }}
  ],
  "treatments": [
    {{
      "type": "тип лечения",
      "description": "описание",
      "date": "дата"
    }}
  ],
  "metadata": {{
    "document_type": "тип документа",
    "institution": "название учреждения",
    "doctor": "ФИО врача",
    "date": "дата документа"
  }}
}}

Если какие-то данные отсутствуют в тексте, оставь поле null. Ответ должен содержать только валидный JSON без дополнительного текста."""

DEFAULT_PROMPT_ANALYZE = """Ты — эксперт по оценке качества медицинской документации. Проанализируй извлечённые данные и подготовь отчёт.

Данные:
{json_data}

Проведи анализ по следующим критериям:

1. **Полнота заполнения**
   - Оцените, насколько полно заполнены обязательные поля
   - Укажите отсутствующие данные

2. **Соответствие стандартам**
   - Проверьте корректность оформления
   - Соответствие формату МКБ для диагнозов

3. **Выявленные проблемы**
   - Противоречия в данных
   - Отсутствие необходимой информации
   - Ошибки оформления

4. **Рекомендации**
   - Что необходимо исправить
   - Что требует уточнения

5. **Общая оценка качества**
   - Числовая оценка от 1 до 10
   - Краткое обоснование

Ответ оформи на русском языке в структурированном виде с использованием Markdown."""

DEFAULT_SYSTEM_EXTRACT = "Ты — медицинский аналитик, специализирующийся на извлечении данных из медицинской документации."
DEFAULT_SYSTEM_ANALYZE = "Ты — эксперт по оценке качества медицинской документации в лечебно-профилактических учреждениях."


def get_prompt_extract() -> str:
    try:
        db = SessionLocal()
        prompt = crud.get_setting(db, "prompt_extract")
        db.close()
        return prompt or DEFAULT_PROMPT_EXTRACT
    except Exception:
        return DEFAULT_PROMPT_EXTRACT


def get_prompt_analyze() -> str:
    try:
        db = SessionLocal()
        prompt = crud.get_setting(db, "prompt_analyze")
        db.close()
        return prompt or DEFAULT_PROMPT_ANALYZE
    except Exception:
        return DEFAULT_PROMPT_ANALYZE


def get_system_extract() -> str:
    try:
        db = SessionLocal()
        prompt = crud.get_setting(db, "system_extract")
        db.close()
        return prompt or DEFAULT_SYSTEM_EXTRACT
    except Exception:
        return DEFAULT_SYSTEM_EXTRACT


def get_system_analyze() -> str:
    try:
        db = SessionLocal()
        prompt = crud.get_setting(db, "system_analyze")
        db.close()
        return prompt or DEFAULT_SYSTEM_ANALYZE
    except Exception:
        return DEFAULT_SYSTEM_ANALYZE


def extract_json_from_text(pdf_text: str, max_tokens: int = -1) -> tuple[Optional[str], Optional[str]]:
    client = get_llm_client()

    if max_tokens == -1:
        max_tokens = None

    try:
        prompt_template = get_prompt_extract()
        prompt = prompt_template.format(pdf_text=pdf_text)
        
        logger.info(f"Extracting JSON, input size: {len(pdf_text)} chars, max_tokens: {max_tokens or 'unlimited'}")
        
        response = client.chat(
            system_prompt=get_system_extract(),
            user_message=prompt,
            max_tokens=max_tokens
        )
        
        logger.info(f"JSON extraction response: finish_reason={response.finish_reason}, truncated={response.truncated}")
        
        if response.truncated:
            logger.warning(f"JSON extraction truncated, finish_reason: {response.finish_reason}")
        
        if not response.content or not response.content.strip():
            logger.error("Empty response from LLM for JSON extraction")
            return None, "LLM вернул пустой ответ"
        
        json_str = response.content.strip()

        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        try:
            parsed = json.loads(json_str)
            result = json.dumps(parsed, ensure_ascii=False, indent=2)
            
            if response.truncated:
                return result, "Предупреждение: ответ был обрезан из-за лимита токенов. Данные могут быть неполными."
            return result, None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return json_str, f"Предупреждение: ответ не является валидным JSON ({str(e)})"

    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        return None, f"Ошибка при извлечении данных: {str(e)}"


def analyze_extracted_data(json_data: str, max_tokens: int = -1) -> tuple[Optional[str], Optional[str]]:
    client = get_llm_client()

    if max_tokens == -1:
        max_tokens = None

    try:
        prompt_template = get_prompt_analyze()
        prompt = prompt_template.format(json_data=json_data)
        
        logger.info(f"Analyzing data, input size: {len(json_data)} chars, max_tokens: {max_tokens or 'unlimited'}")
        
        response = client.chat(
            system_prompt=get_system_analyze(),
            user_message=prompt,
            max_tokens=max_tokens
        )
        
        logger.info(f"Analysis response: finish_reason={response.finish_reason}, truncated={response.truncated}, content_length={len(response.content) if response.content else 0}")
        
        if response.truncated:
            logger.warning(f"Analysis truncated, finish_reason: {response.finish_reason}")
            if response.content:
                return response.content, "Предупреждение: аналитика была обрезана из-за лимита токенов. Попробуйте уменьшить количество документов."
            else:
                return None, "Аналитика была обрезана и пуста. Попробуйте уменьшить количество документов."
        
        if not response.content or not response.content.strip():
            logger.error("Empty response from LLM for analysis")
            return None, "LLM вернул пустой ответ при анализе"
        
        return response.content, None

    except Exception as e:
        logger.error(f"Error analyzing data: {e}", exc_info=True)
        return None, f"Ошибка при анализе данных: {str(e)}"


def process_pdf_text(pdf_text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    json_result, json_error = extract_json_from_text(pdf_text)
    if json_error and not json_result:
        return None, None, json_error

    analysis_result, analysis_error = analyze_extracted_data(json_result or "{}")
    if analysis_error:
        return json_result, None, analysis_error

    return json_result, analysis_result, None
