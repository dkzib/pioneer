import io
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from dotenv import load_dotenv

from db import (
    db_add, get_all_items,
    update_items_status,
    get_info_out_items,
    get_info_low_items
)
from genai_stop import parse_stoplist_message
from genai_doc import parse_receipt_image
from settings import DOCUMENTS_CHAT_ID, STOP_LIST_CHAT_ID, ID_STOP_LIST
from log import logger


load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("stoplist"))
async def cmd_stoplist(message: Message):
    """Команда /stoplist для вывода актуальных стопов в чат."""

    user = message.from_user.full_name
    logger.info(f'Пользователь [{user}] ввёл команду /stoplist.')

    out_items = get_info_out_items()
    low_items = get_info_low_items()

    if not out_items and not low_items:
        await message.answer("✅ Все позиции есть в наличии. Стоп-лист пуст!")
        return

    answer = "<b>Актуальный стоп-лист:</b>\n"
    for item in out_items:
        answer += f"⛔️ {item}\n"

    if low_items:
        answer += '\n<b>Заканчиваются:</b>\n'
        for item in low_items:
            answer += f"⚠️ {item}\n"

    await message.answer(f'{answer}', parse_mode="HTML")


@dp.message(F.chat.id == STOP_LIST_CHAT_ID)
async def handle_group_message(message: types.Message):
    """Работа с сообщениями беседы СТОП ЛИСТ."""

    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):

        user = message.from_user.full_name
        username = message.from_user.first_name
        text = message.text
        logger.info(
            f'Сообщение [{text}] от пользователя [{user}]'
        )

        if message.message_thread_id == ID_STOP_LIST:
            db_add(
                username=message.from_user.first_name,
                message=message.text,
                user_id=message.from_user.id,
                reply_message=message.reply_to_message.text,
                datetime=message.date,
                message_id=message.message_id
            )

            available_items = get_all_items()  # вся номенклатура в переменной

            parsed = parse_stoplist_message(text, available_items)  # вызов ИИ

            conf = parsed.get('confidence', 0)  # уверенность в ответе
            if conf <= 7:                       # реакция на сообщение
                logger.warning(                 # если низкая уверенность
                    f'Бот не уверен! conf = {conf}. Изменения в БД отменены.'
                )
                await message.react([types.ReactionTypeEmoji(emoji="🤷‍♂️")])
                return

            stop_items = parsed.get("out_of_stock", [])  # распарсинг ответа ИИ
            low_items = parsed.get("running_low", [])
            in_items = parsed.get("in_stock", [])

            if stop_items:
                update_items_status(stop_items, status=0, username=username)
            if low_items:
                update_items_status(low_items, status=1, username=username)
            if in_items:
                update_items_status(in_items, status=2, username=username)

            conf = parsed.get('confidence')  # уверенность бота в ответе
            if conf <= 7:
                logger.warning(f'Бот не уверен! conf = {conf}')


@dp.message((F.chat.id == DOCUMENTS_CHAT_ID) & (F.photo))
async def handle_document_chat_message(message: types.Message):
    """Работа с сообщениями беседы ОТЧЕТЫ."""

    username = message.from_user.full_name
    logger.info(f'Пользователь [{username}] отправил фото в беседу "отчёты".')
    try:  # скачивание и обработка фото в нейронке
        logger.info('Попытка скачивания и обработки фото через gAPI.')
        available_items = get_all_items()
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        image_io = io.BytesIO()
        await bot.download_file(file_info.file_path, destination=image_io)
        image_io.seek(0)
        parsed_data = parse_receipt_image(image_io, available_items)

        items_from_receipt = parsed_data.get("items", [])
        print(items_from_receipt)

        username = message.from_user.first_name
        items_to_update = []
        for item in items_from_receipt:     # формирование списка для
            item_name = item.get("name")    # обновления позиций в БД
            if item_name in available_items:
                items_to_update.append(item_name)

        if items_to_update:                 # обновление статуса в БД
            update_items_status(
                items=items_to_update,
                status=2,
                username=username
            )
            logger.info('Обновлены статусы в БД.')
        else:
            logger.warning('Накладная не распознана!')

    except Exception as e:
        logger.error(f'Непредвиденная ошибка при обработке чека. Ошибка: {e}')
        #  await message.react([types.ReactionTypeEmoji(emoji="❌")])
        await message.reply(
            "Не удалось обработать изображение. Убедитесь, что чек четкий."
        )
