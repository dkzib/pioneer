import json
import io
import time
from log import logger

from google import genai
from google.genai import types
from google.genai.errors import APIError
from PIL import Image

from keys import GEMINI_API_KEY
from constants import get_doc_prompt


ai_client = genai.Client(api_key=GEMINI_API_KEY)


def parse_receipt_image(image_bytes: io.BytesIO, known_items) -> dict:
    """Отправляет изображение в Gemini и парсит JSON."""

    image = Image.open(image_bytes)

    for attempt in range(1, 6):

        try:
            logger.info(f'Попытка [{attempt}/6] запроса к gAPI.')
            response = ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[image, get_doc_prompt(known_items)],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            parsed_data = json.loads(response.text)
            formatted_json = json.dumps(parsed_data, indent=2, ensure_ascii=False)
            logger.info(f'Ответ получен успешно. Попытка [{attempt}/6]')
            logger.debug(f"Ответ от модели:\n{formatted_json}")
            return parsed_data

        except APIError as error:
            logger.error(f'gAPI не дал ответ. Ошибка {error.code}. Попытка [{attempt}/6]')
            time.sleep(2)

    logger.warning('Был возвращен пустой список-заглушка. genai-doc')
    return {"items": [], "total_sum": 0, "confidence": 0}
