import hvac 
import os 
import requests
from logger import logger
import sys

# client = hvac.Client(
#     url='https://vault.bakvivas.ru',
#     token=os.environ['VAULT_TOKEN'],
#     verify="/etc/ssl/certs/ca-certificates.crt"
# )

# if client.is_authenticated():
#     print("true")
# else:
#     print("false")

# read_secret_result = client.secrets.kv.v2.read_secret(
#     path="zazatappo-vacanzi/database",
#     mount_point="kv2"
# )

def create_client(url, token_name, verify_path):
    try:
        logger.debug(f"Пробую подключиться к хранилищу vault")
        client = hvac.Client(
            url=url,
            token=os.environ[token_name],
            verify=verify_path
        )
    except Exception as e:
        logger.error(f"Ошибка подключения к vault: {e}")
        sys.exit(1)

    logger.debug(f"Проверка подключения к пользователю vault: {client.is_authenticated()}")
    return client 

def get_database_secrets(path, mount_point, client):
    database_secrets = {
        "dbname": None,
        "user": None,
        "password": None,
        "host": None,
        "port": None
    }

    try:
        logger.debug(f"Получаю данные по пути {path} для подключения к базе данных")
        read_secret_result = client.secrets.kv.v2.read_secret(
            path=path,
            mount_point=mount_point
        )
    except Exception as e:
        logger.error(f"Ошибка получения данных по пути {path} для подключения к базе данных: {e}")
        sys.exit(1)

    database_secrets["dbname"] = read_secret_result["data"]["data"]["dbname"]
    database_secrets["user"] = read_secret_result["data"]["data"]["user"]
    database_secrets["password"] = read_secret_result["data"]["data"]["password"]
    database_secrets["host"] = read_secret_result["data"]["data"]["host"]
    database_secrets["port"] = read_secret_result["data"]["data"]["port"]

    return database_secrets

# print(read_secret_result)
