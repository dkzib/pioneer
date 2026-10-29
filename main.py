import asyncio

from handlers import bot, dp
from log import logger
from db import db_init


async def main():
    logger.info('Бот запущен.')
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

 
if __name__ == "__main__":
    db_init()
    asyncio.run(main())
