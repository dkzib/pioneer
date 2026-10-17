import json
import io

from google import genai
from google.genai import types
from PIL import Image

from constants import get_doc_prompt, GEMINI_API_KEY


ai_client = genai.Client(api_key=GEMINI_API_KEY)


def parse_receipt_image(image_bytes: io.BytesIO, known_items) -> dict:
    """Отправляет изображение в Gemini и парсит JSON."""

    image = Image.open(image_bytes)

    response = ai_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[image, get_doc_prompt(known_items)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    #  print(json.loads(response.text))
    return json.loads(response.text)


# with open("receipt.jpg", "rb") as f:
#     image_bytes = io.BytesIO(f.read())

#  parse_receipt_image(image_bytes)
