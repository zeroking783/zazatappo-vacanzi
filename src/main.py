from get_vacancies import get_vacancies
from connect_db import connect_database

def main():
    vacancies = get_vacancies()
    print(len(vacancies))

    # try:
    conn, cur = connect_database("91.222.238.14", "6432", "auto_cv_db", "auto_cv_user", "password")
    # # except Exception as e:
    #     # print(f"Ошибка подключения к базе данных: {e}")

    query_insert = (
        "INSERT INTO vacancies (id, link_num, name, subdivision, date_pub, sity, description, no_experience) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    for vacancy in vacancies:
        print("========================")
        print(vacancy)

        cur.execute("SELECT COUNT(*) FROM vacancies WHERE link_num = %s", (vacancy["link_num"],))
        count = cur.fetchone()[0]

        if count == 0:
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
        else:
            print(f"Запись с link_num = {vacancy["link_num"]} уже существует в таблице")
    cur.close()
    conn.close()


    

if __name__ == '__main__':
    main()