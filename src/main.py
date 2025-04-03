from get_vacancies import get_vacancies
from connect_db import connect_database
from vault import create_client, get_database_secrets
from logger import logger
import schedule
import time
import sys
from pathlib import Path
import atexit
import signal

lock_path = Path("/tmp/zaza.lock")

def cleanup_lock():
    if lock_path.exists():
        try:
            lock_path.unlink()
            logger.info("Удалён lock-файл")
        except Exception as e:
            logger.warning(f"Ошибка удаления lock-файла: {e}")

atexit.register(cleanup_lock)

def handle_exit(signum, frame):
    logger.info(f"Получен сигнал завершения ({signum}), выхожу...")
    cleanup_lock()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def main():
    try:
        with open(lock_path, 'x'):
            logger.debug("Создан lock-файл")
    except FileExistsError:
        logger.warning("Прошлый запуск ещё выполняется — пропускаю цикл")
        return

    logger.info("Начинаю новый цикл")

    try:
        vacancies = get_vacancies()

        client = create_client(
            url="https://vault.bakvivas.ru",
            token_name="VAULT_TOKEN",
            verify_path="/etc/ssl/certs/ca-certificates.crt"
        )

        database_secrets = get_database_secrets(
            path="zazatappo-vacanzi/database",
            mount_point="kv2",
            client=client
        )

        conn, cur = connect_database(database_secrets)

        query_insert = (
            "INSERT INTO vacancies (id, link_num, name, subdivision, date_pub, sity, description, no_experience, actual) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )

        for vacancy in vacancies:
            try:
                cur.execute(query_insert, (
                    str(vacancy["id"]),
                    vacancy["link_num"],
                    vacancy["name"],
                    vacancy["subdivision"],
                    vacancy["date_pub"],
                    vacancy["sity"],
                    vacancy["description"],
                    vacancy["no_experience"],
                    True
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Ошибка вставки в БД: {e}")
                conn.rollback()
                continue

        logger.info("Закрываю соединение с БД")
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка в main(): {e}")

    finally:
        cleanup_lock()

if __name__ == '__main__':
    logger.info("Запускаю программу")
    main()
    schedule.every(5).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(5)
