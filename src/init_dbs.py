from vacancies.models import create_tables
from loguru import logger
from vacancies.connect_to_hhru import get_vacancies_data

logger.add("log/info.log", format="{time} {level} {message}", level="INFO")

logger.info("База создана")


create_tables()

# get_vacancies_data("Python")