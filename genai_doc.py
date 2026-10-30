import json
import io
import time
import os

from dotenv import load_dotenv
from log import logger
from google import genai
from google.genai.errors import APIError
from PIL import Image

from constants import get_doc_prompt, get_gemini_config
from settings import CURRENT_MODEL


load_dotenv()
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def parse_receipt_image(image_bytes: io.BytesIO, known_items) -> dict:
    """Отправляет изображение в Gemini и парсит JSON."""

    image = Image.open(image_bytes)

    for attempt in range(1, 6):

        try:
            logger.info(f'Попытка [{attempt}/5] запроса к gAPI.')
            response = ai_client.models.generate_content(
                model=CURRENT_MODEL,
                contents=[image, get_doc_prompt(known_items)],
                config=get_gemini_config(CURRENT_MODEL)
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
            logger.error(
                f'gAPI не ответил. Ошибка {error.code}. Попытка [{attempt}/5]'
            )
            time.sleep(2)

        except (json.JSONDecodeError, TypeError, Exception) as error:
            logger.error(f'Ошибка парсинга ответа. Ошибка: {error}')
            break

    logger.warning('Был возвращен пустой список-заглушка. genai-doc')
    return {"items": [], "total_sum": 0, "confidence": 0}
