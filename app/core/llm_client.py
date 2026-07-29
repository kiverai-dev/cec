from typing import Optional
import logging
import httpx
from app.core.schemas import LLMRequest, LLMResponse
from app.database.session import SessionLocal
from app.database import crud
from app.config import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url
        self.model_name = model_name
        self.api_key = api_key
        self.timeout = 300.0

    def _get_settings(self) -> dict:
        try:
            db = SessionLocal()
            settings = crud.get_all_settings(db)
            db.close()
            return settings
        except Exception:
            return DEFAULT_SETTINGS

    def _get_base_url(self) -> str:
        if self.base_url:
            return self.base_url
        settings = self._get_settings()
        return settings.get("api_url", DEFAULT_SETTINGS["api_url"])

    def _get_model_name(self) -> str:
        if self.model_name:
            return self.model_name
        settings = self._get_settings()
        return settings.get("model_name", DEFAULT_SETTINGS["model_name"])

    def _get_api_key(self) -> Optional[str]:
        if self.api_key:
            return self.api_key
        settings = self._get_settings()
        return settings.get("api_key", DEFAULT_SETTINGS.get("api_key"))

    def _get_temperature(self) -> float:
        settings = self._get_settings()
        return float(settings.get("temperature", DEFAULT_SETTINGS["temperature"]))

    def _get_max_tokens(self) -> int:
        settings = self._get_settings()
        return int(settings.get("max_tokens", DEFAULT_SETTINGS["max_tokens"]))

    def chat(self, system_prompt: str, user_message: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        base_url = self._get_base_url().rstrip("/")
        url = f"{base_url}/v1/chat/completions"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        actual_temperature = temperature if temperature is not None else self._get_temperature()
        
        payload = {
            "model": self._get_model_name(),
            "messages": messages,
            "temperature": actual_temperature
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {"Content-Type": "application/json"}
        api_key = self._get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        logger.info(f"LLM request: model={self._get_model_name()}, max_tokens={max_tokens or 'unlimited'}, temp={actual_temperature}")
        logger.debug(f"User message length: {len(user_message)} chars")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            logger.error(f"LLM request timed out after {self.timeout}s")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            raise

        content = data["choices"][0]["message"]["content"]
        model = data.get("model", self._get_model_name())
        usage = data.get("usage")
        finish_reason = data["choices"][0].get("finish_reason")
        truncated = finish_reason == "length"

        logger.info(f"LLM response: finish_reason={finish_reason}, truncated={truncated}, usage={usage}, content_length={len(content) if content else 0}")

        if truncated:
            logger.warning(f"Response truncated! finish_reason={finish_reason}")

        return LLMResponse(content=content, model=model, usage=usage, finish_reason=finish_reason, truncated=truncated)

        return LLMResponse(content=content, model=model, usage=usage, finish_reason=finish_reason, truncated=truncated)

    def test_connection(self) -> tuple[bool, str]:
        try:
            base_url = self._get_base_url().rstrip("/")
            
            headers = {}
            api_key = self._get_api_key()
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            test_payload = {
                "model": self._get_model_name(),
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{base_url}/v1/chat/completions",
                    json=test_payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return True, "Соединение успешно"
                elif response.status_code == 401:
                    return False, "Ошибка авторизации: проверьте API ключ"
                elif response.status_code == 404:
                    return False, "Endpoint не найден: проверьте URL API"
                else:
                    return False, f"Ошибка: статус {response.status_code}"
                    
        except httpx.ConnectError:
            return False, "Не удалось подключиться к серверу"
        except httpx.TimeoutException:
            return False, "Превышено время ожидания"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"


def get_llm_client() -> LLMClient:
    return LLMClient()
