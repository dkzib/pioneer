from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType
import asyncio
from db import db_init, db_add, get_all_items, update_items_status, get_info_out_items, get_info_low_items
from genai_stop import parse_stoplist_message
from constants import DOCUMENTS_CHAT_ID, STOP_LIST_CHAT_ID, BOT_TOKEN, ID_STOP_LIST
from genai_doc import parse_receipt_image
import io


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("stoplist"))
async def cmd_stoplist(message: Message):
    """Команда /stoplist для вывода актуальных стопов в чат."""
    out_items = get_info_out_items()
    low_items = get_info_low_items()

    if not out_items and not low_items:
        await message.answer("✅ На данный момент все позиции есть в наличии. Стоп-лист пуст!")
        return

    answer = "<b>Актуальный стоп-лист:</b>\n"
    for item in out_items:
        answer += f"⛔️ {item}\n"

    if low_items:
        answer += '\n<b>Заканчиваются</b>\n'
        for item in low_items:
            answer += f"⚠️ {item}\n"

    await message.answer(f'{answer}', parse_mode="HTML")

#⛔️

#⚠️







@dp.message(F.chat.id == STOP_LIST_CHAT_ID)
async def handle_group_message(message: types.Message):
    """Работа с сообщениями беседы СТОП ЛИСТ."""

    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        print(f"Сообщение от {message.from_user.full_name}: {message.text}")

        username = message.from_user.first_name
        text = message.text

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
                print(f'бот неуверен в ответе!!! conf = {conf}.')


@dp.message((F.chat.id == DOCUMENTS_CHAT_ID) & (F.photo))
async def handle_document_chat_message(message: types.Message):
    """Работа с сообщениями беседы ОТЧЕТЫ."""

    try:  # скачивание и обработка фото в нейронке
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
            print(f"📦 Обновлены статусы в БД для: {items_to_update}")
        else:
            print('Накладная не распознана!')

    except Exception as e:
        print(f"Ошибка при обработке чека: {e}")
        #  await message.react([types.ReactionTypeEmoji(emoji="❌")])
        await message.reply("Не удалось обработать изображение. Убедитесь, что чек четкий.")


async def main():
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    db_init()
    asyncio.run(main())
