from models import create_tables
from loguru import logger

logger.add("log/info.log", format="{time} {level} {message}", level="INFO")

logger.info("База создана")


create_tables()

