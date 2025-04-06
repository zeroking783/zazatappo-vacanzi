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
import csv 


parser_runs = Counter("vacancy_parser_runs_total", "Общее количество запусков парсера")
all_vacancies_gauge = Gauge("vacancy_parser_all_vacancies", "Количество выложенных вакансий на текущий момент времени")
now_running = Gauge("vacancy_parser_now_running", "В данный момент времени происходит процесс парсинга и сохранение")
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
    try:
        logger.debug(f"Получаю список активных вакансий из базы данных")
        cur.execute(query_get_active_vacancies)
    except Exception as e:
        logger.warning(f"Ошибка получения списка активных вакансий из базы данных: {e}")
    active_vacancies = {str(row[0]) for row in cur.fetchall()}

    current_vacancies_link_nums = {str(vacancy["link_num"]) for vacancy in current_vacancies}

    inactive_vacancies = [i for i in active_vacancies if i not in current_vacancies_link_nums]

    if inactive_vacancies:
        query_update_inactive = "UPDATE vacancies SET actual = FALSE WHERE link_num IN %s"
        try:
            logger.debug(f"Обновляю неактуальные вакансии в базе данных")
            cur.execute(query_update_inactive, (tuple(inactive_vacancies),))
            conn.commit()
        except Exception as e:
            logger.warning(f"Ошибка обновления неактуальных вакансий в базе данных: {e}")
        logger.info(f"Обновлено {len(inactive_vacancies)} неактуальных вакансий на 'actual = false'")


def load_fake_vacancies(csv_file):
    fake_vacancies = []

    if not Path(csv_file).exists():
        logger.warning(f"Файл {csv_file} с фейковыми вакансиями не найден!")
        return fake_vacancies
    
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        logger.debug(f"Читаю файл с фейковыми вакансиями")
        reader = csv.DictReader(csvfile)
        for row in reader:
            fake_vacancies.append({
                "id": row['id'],
                "link_num": row['link_num'],
                "name": row['name'],
                "subdivision": row['subdivision'],
                "date_pub": row['date_pub'],
                "sity": row['sity'],
                "description": row['description'],
                "no_experience": row['no_experience'].lower() == 'true'
            })
    
    return fake_vacancies


def main():

    try:
        with open(lock_path, 'x'):
            logger.debug("Создан lock-файл")
    except FileExistsError:
        logger.warning("Прошлый запуск ещё выполняется — пропускаю цикл")
        return

    logger.info("Начинаю новый цикл")
    parser_runs.inc()
    now_running.set(1)

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

        # fake_vacancies = load_fake_vacancies("fake_vacancies.csv")

        # vacancies = fake_vacancies

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
        
        now_running.set(0)


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
