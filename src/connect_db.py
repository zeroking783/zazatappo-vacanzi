import psycopg2 
from logger import logger
import sys

def connect_database(database_secrets):
    try:
        logger.debug(f"Пробую подключиться к базе данных")
        conn = psycopg2.connect(
            dbname=database_secrets["dbname"],
            user=database_secrets["user"],
            password=database_secrets["password"],
            host=database_secrets["host"],
            port=database_secrets["port"]
        )
    except Exception as e:
        logger.error(f"Безуспешное подключение к базе данных: {e}")
        continue

    try:
        logger.debug(f"Создаю объект база данных cursor")
        cur = conn.cursor()
    except Exception as e:
        logger.error(f"Ошибка создания объекта cursor: {e}")
        continue

    logger.debug(f"Объекты для подключения к базе данных успешно созданы")

    return conn, cur