import json
from google import genai
from google.genai import types

from constants import get_stop_prompt, GEMINI_API_KEY


ai_client = genai.Client(api_key=GEMINI_API_KEY)


def parse_stoplist_message(message_text, known_items):
    """Анализирует текст сообщения и сопоставляет его со списком товаров."""

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

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return {"out_of_stock": [], "running_low": [], "in_stock": []}
