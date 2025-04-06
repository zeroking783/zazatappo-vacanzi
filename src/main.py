from get_vacancies import get_vacancies
from connect_db import connect_database
from vault import create_client, get_database_secrets
from logger import logger
import schedule
import time
import datetime
import sys
from pathlib import Path
import atexit
import signal
from prometheus_client import start_http_server, Counter, Gauge, Summary


parser_runs = Counter("vacancy_parser_runs_total", "Общее количество запусков парсера")
all_vacancies_gauge = Gauge("vacancy_parser_all_vacancies", "Количество выложенных вакансий на текущий момент времени")
proces_duration = Summary("vacancy_parser_proces_duration", "Время обработки процесса парсинга (секунды)")
last_send_vacancies_data_base = Gauge("vacancy_parser_last_send_vacancies_data_base", "Последнее отправление спаршенных вакансий в базу данных")


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

def update_inactive_vacancies(conn, cur, current_vacancies):
    query_get_active_vacancies = "SELECT link_num FROM vacancies WHERE actual = TRUE"
    cur.execute(query_get_active_vacancies)
    active_vacancies = {row[0] for row in cur.fetchall()}
    logger.info(f"ACTIVE_VACANCIES: {active_vacancies}")

    current_vacancies_link_nums = {vacancy["link_num"] for vacancy in current_vacancies}
    logger.info(f"CURRENT VACANCIES LINK NUMS: {current_vacancies_link_nums}")

    query_update_inactive = "UPDATE vacancies SET actual = FALSE WHERE link_num IN %s"

    inactive_vacancies = [i for i in active_vacancies if i not in current_vacancies_link_nums]

    if inactive_vacancies:
        query_update_inactive = "UPDATE vacancies SET actual = FALSE WHERE link_num IN %s"
        cur.execute(query_update_inactive, (tuple(inactive_vacancies),))
        conn.commit()
        logger.info(f"Обновлено {len(inactive_vacancies)} вакансий на 'actual = false'")


def main():
    parser_runs.inc()
    try:
        with open(lock_path, 'x'):
            logger.debug("Создан lock-файл")
    except FileExistsError:
        logger.warning("Прошлый запуск ещё выполняется — пропускаю цикл")
        return

    logger.info("Начинаю новый цикл")

    start_time = time.time()

    try:
        vacancies = get_vacancies()
        count_vacancies = len(vacancies)
        all_vacancies_gauge.set(count_vacancies)

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
                timestamp_seconds = int(datetime.datetime.now().timestamp())
                last_send_vacancies_data_base.set(timestamp_seconds)
            except Exception as e:
                logger.error(f"Ошибка вставки в БД: {e}")
                conn.rollback()
                continue

        update_inactive_vacancies(conn, cur, vacancies)

        logger.info("Закрываю соединение с БД")
        proces_duration.observe(time.time() - start_time)

    except Exception as e:
        logger.error(f"Ошибка в main(): {e}")

    finally:

        if cur:
            try:
                cur.close()
            except Exception as e:
                logger.warning(f"Не удалось закрыть cursor: {e}")

        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Не удалось закрыть соединение с БД: {e}")

        cleanup_lock()


if __name__ == '__main__':
    logger.info("Запускаю программу")
    
    try:
        logger.info("Запускаю http сервер для логов")
        start_http_server(8000)
    except Exception as e:
        logger.error(f"Ошибка запуска http сервера: {e}")

    main()
    schedule.every(5).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(5)
