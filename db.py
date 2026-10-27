import sqlite3
from datetime import datetime
import os
import json
from log import logger


def db_init():

    connection = sqlite3.connect('pioneer.db')

    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        message TEXT,
        user_id INTEGER,
        reply_message TEXT,
        datetime TEXT,
        message_id INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL UNIQUE,
        status INTEGER NOT NULL DEFAULT 2,
        last_update_time TEXT,
        last_update_user TEXT
    )
    ''')

    cursor.execute('SELECT COUNT(*) FROM items')
    count = cursor.fetchone()[0]

    if count == 0:
        fixture_path = 'fixtures.json'
        if os.path.exists(fixture_path):
            with open(fixture_path, 'r', encoding='utf-8') as f:
                fixtures_data = json.load(f)
                
                for entry in fixtures_data:
                    item_name = entry.get("item")
                    item_status = entry.get("status", 2) # Берем статус из фикстуры (по умолчанию 2)
                    
                    cursor.execute('''
                        INSERT INTO items (item, status) 
                        VALUES (?, ?)
                    ''', (item_name, item_status))

            logger.info(f'БД не обнаружена. Создание и заполнение из фикстуры.')
            logger.info(f'Из фикстуры загружено {len(fixtures_data)} позиций.')
            #print(f"🚀 Первый запуск: база заполнена из фикстуры ({len(fixtures_data)} поз.)")
        else:
            logger.critical(f'Файл фикстуры {fixture_path} не найден!')
            #print(f"⚠️ Файл фикстуры {fixture_path} не найден!")
    else:
        logger.info(f'Файл БД найден. Пропуск загрузки фикстуры.')
        #print("✅ База уже инициализирована, пропускаем загрузку фикстуры.")

    connection.commit()
    connection.close()


def db_add(username, message, user_id, reply_message, datetime, message_id):
    connection = sqlite3.connect('pioneer.db')
    cursor = connection.cursor()

    cursor.execute('''
    INSERT INTO users (username, message, user_id, reply_message, datetime, message_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, message, user_id, reply_message, datetime, message_id))

    connection.commit()
    connection.close()


def get_info_db():
    connection = sqlite3.connect('pioneer.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    connection.close()


#  0 - отсутствует на складе (стоп)
#  1 - заканчивается на складе (мало)
#  2 - есть на складе


def get_all_items():
    """Возвращает список всех позиций из базы."""
    connection = sqlite3.connect('pioneer.db')
    cursor = connection.cursor()
    cursor.execute('SELECT item FROM items')
    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]


def update_items_status(items, status, username):
    """Меняет статус для переданного списка товаров и возвращает новые."""
    if not items:  # если список пустой, то не тратим ресурсы
        return []

    connection = sqlite3.connect('pioneer.db')
    cursor = connection.cursor()
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # updated = []

    for item in items:
        cursor.execute(
            '''
            UPDATE items
            SET status = ?, last_update_time = ?, last_update_user = ?
            WHERE item = ?
            ''',
            (status, now_time, username, item)
        )
        # if cursor.rowcount > 0:
        #     updated.append(item)

    connection.commit()
    connection.close()
    # return updated


def get_info_out_items():
    """Возвращает список всех закончившихся позиций в базе."""
    connection = sqlite3.connect('pioneer.db')
    cursor = connection.cursor()

    cursor.execute('SELECT item FROM items WHERE status = 0')
    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]


def get_info_low_items():
    """Возвращает список всех заканчивающихся позиций в базе."""
    connection = sqlite3.connect('pioneer.db')
    cursor = connection.cursor()

    cursor.execute('SELECT item FROM items WHERE status = 1')
    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]
