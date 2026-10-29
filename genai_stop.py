import json
import time
import os

from dotenv import load_dotenv
from log import logger
from google import genai
from google.genai import types
from google.genai.errors import APIError

from constants import get_stop_prompt


load_dotenv()
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def parse_stoplist_message(message_text, known_items):
    """Анализирует текст сообщения и сопоставляет его со списком товаров."""

    for attempt in range(1, 6):
        try:
            logger.info(f'Попытка [{attempt}/5] запроса к gAPI.')
            response = ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=get_stop_prompt(
                    known_items=known_items,
                    message_text=message_text
                ),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                ),
            )

            parsed_data = json.loads(response.text)
            formatted_json = json.dumps(
                parsed_data,
                indent=2,
                ensure_ascii=False
            )

            logger.info(f'Ответ получен успешно. Попытка [{attempt}/5]')
            logger.debug(f"Ответ от модели:\n{formatted_json}")
            return parsed_data

        except APIError as error:
            logger.warning(
                f'gAPI не ответил. Ошибка {error.code}. Попытка [{attempt}/5]'
            )
            time.sleep(2)

        except (json.JSONDecodeError, TypeError, Exception) as error:
            logger.error(f'Ошибка парсинга ответа. Ошибка: {error}')
            break

    logger.warning('Был возвращен пустой список-заглушка. genai-stop')
    return {
        "out_of_stock": [],
        "running_low": [],
        "in_stock": [],
        "confidence": 0
    }
