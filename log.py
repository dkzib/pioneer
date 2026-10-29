import logging

# Базовая конфигурация: куда писать и в каком формате
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Сохраняет в файл
        logging.StreamHandler()                            # Выводит в консоль
    ]
)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Создаем глобальный объект логгера
logger = logging.getLogger("pioneer")
