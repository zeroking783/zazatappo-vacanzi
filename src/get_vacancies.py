from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import sys
import uuid
import time

def get_vacancies():
    vacancies_dict = []

    month_mapping = {
        "января": "01", "февраля": "02", "марта": "03", "апреля": "04", "мая": "05",
        "июня": "06", "июля": "07", "августа": "08", "сентября": "09", "октября": "10",
        "ноября": "11", "декабря": "12"
    }

    options = webdriver.FirefoxOptions()
    driver = webdriver.Firefox(options=options)

    driver.get("https://rabota.sber.ru/search/?query=DevOps")

    scroll_pause_time = 2

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(scroll_pause_time)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break 
        last_height = new_height
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    vacancies = driver.find_elements(By.XPATH, "//div[contains(@class, 'styled__Card-sc-192d1yv-1 fmUtEX')]")

    for vacancy in vacancies:
        vacancy_dict = {
            "id": uuid.uuid4(),
            "link_num": None,
            "name": None,
            "subdivision": None,
            "date_pub": None,
            "sity": None,
            "description": None,
            "no_experience": False,
        }

        try:
            name = vacancy.find_element(By.XPATH, ".//div[contains(@class, 'Text-sc-36c35j-0 iUPRtQ')]").text
            if name:
                vacancy_dict["name"] = name
        except Exception as e:
            print(f"Ошибка с парсингом имени вакансии: {e}")
            sys.exit(1)

        try:
            subdivision = vacancy.find_elements(By.XPATH, ".//div[contains(@class, 'Text-sc-36c35j-0 bYzNBd')]")[1].text
            if subdivision:
                vacancy_dict["subdivision"] = subdivision
        except Exception as e:
            print(f"Ошибка с парсингом подразделения: {e}")
            sys.exit(1)
        
        try:
            date_pub = vacancy.find_element(By.XPATH, ".//div[contains(@class, 'Text-sc-36c35j-0 cMyOwV')]").text
            if date_pub:
                date_pub_list = date_pub.split(" ")
                month_str = date_pub_list[1]
                month_num = month_mapping[month_str]
                date_pub = date_pub_list[2] + "-" + month_num + "-" + date_pub_list[0]
                vacancy_dict["date_pub"] = date_pub
        except Exception as e:
            print(f"Ошибка с парсингом даты публикации вакансии: {e}")
            sys.exit(1)

        try:        
            sity = vacancy.find_elements(By.XPATH, ".//div[contains(@class, 'Text-sc-36c35j-0 bYzNBd')]")[0].text
            if sity:
                vacancy_dict["sity"] = sity
        except Exception as e:
            print(f"Ошибка с парсингом города работы: {e}")
            sys.exit(1)

        try:
            description = vacancy.find_element(By.XPATH, ".//div[contains(@class, 'styled__IntroContainer-sc-192d1yv-11 gjoQSZ')]").text
            if description:
                vacancy_dict["description"] = description
        except Exception as e:
            print(f"Ошибка с парсингом описания: {e}")
            sys.exit(1)

        try:    
            experience = vacancy.find_element(By.XPATH, ".//div[contains(@class, 'styled__Chip-sc-1czfvi7-0 styled__ChipBlock-sc-192d1yv-9 gaZFxD')]").text
            if experience:
                vacancy_dict["no_experience"] = True
        except NoSuchElementException:
            vacancy_dict["no_experience"] = False
        except Exception as e:
            print(f"Ошибка с парсингом необходимости опыта: {e}")
            sys.exit(1)
        
        try:
            link = vacancy.find_element(By.XPATH, ".//a").get_attribute("href")
            link = link.split('/')
            link = link[-1]
            if link:
                vacancy_dict["link_num"] = link
        except Exception as e:
            print(f"Ошибка с парсингом ссылки вакансии: {e}")
            sys.exit(1)

        vacancies_dict.append(vacancy_dict)

    driver.quit()
    return vacancies_dict