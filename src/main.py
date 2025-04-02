from get_vacancies import get_vacancies
from connect_db import connect_database
from vault import create_client, get_database_secrets
from logger import logger
import schedule
import time

is_running = False

def main():
    global is_running

    if is_running:
        logger.warning(f"Прошлый запуск не завершен, пропускаю текущий цикл")
        sys.exit(1)
        return

    is_running = True

    vacancies = get_vacancies()
    logger.debug(f"Найдено {len(vacancies)} вакансий")

    client = create_client(url="https://vault.bakvivas.ru", token_name="VAULT_TOKEN", verify_path="/etc/ssl/certs/ca-certificates.crt")

    database_secrets = get_database_secrets(path="zazatappo-vacanzi/database", mount_point="kv2", client=client)

    conn, cur = connect_database(database_secrets)

    query_insert = (
        "INSERT INTO vacancies (id, link_num, name, subdivision, date_pub, sity, description, no_experience) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    for vacancy in vacancies:
        # print("========================")
        # print(vacancy)

        try:
            cur.execute("SELECT COUNT(*) FROM vacancies WHERE link_num = %s", (vacancy["link_num"],))
        except Exception as e:
            logger.error(f"Не удалось выполнить запрос в базу данных: {e}")
            sys.exit(1)

        count = cur.fetchone()[0]

        if count == 0:
            try:
                cur.execute(query_insert, (
                    str(vacancy["id"]),
                    vacancy["link_num"],
                    vacancy["name"],
                    vacancy["subdivision"],
                    vacancy["date_pub"],
                    vacancy["sity"],
                    vacancy["description"],
                    vacancy["no_experience"]
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Не удалось выполнить запрос в базу данных")
                sys.exit(1)
        else:
            try:
                cur.execute("SELECT id, name, subdivision, date_pub, link_num FROM vacancies WHERE link_num = %s", (vacancy["link_num"],))
                results = cur.fetchall()
                if results:
                    for row in results:
                        vacancy_id, name, subdivision, date_pub, link_num = row
                        name = name.strip()
                        date_pub = str(date_pub)
                        link_num = str(link_num)
                        subdivision = subdivision.strip()
                        if vacancy["name"] != name or vacancy["subdivision"] != subdivision or vacancy["date_pub"] != date_pub:
                            logger.debug(f"Разные вакансии с одной ссылкой")
                            logger.debug(f"Вакансия в базе данных: {vacancy_id}, {name}, {subdivision}, {date_pub}, {link_num}")
                            logger.debug(f"Новая вакансия: {vacancy["id"]}, {vacancy["name"]}, {vacancy["subdivision"]}, {vacancy["date_pub"]}, {vacancy["link_num"]}")
            except Exception as e:
                logger.error(f"Ошибка получения вакансий с одной ссылкой")
                sys.exit(1)

    try:
        logger.debug(f"Закрываю cur и conn")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка закрытия cur и conn: {e}")

    is_running = False

if __name__ == '__main__':
    logger.info(f"Запускаю программу")
    schedule.every(5).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(5)