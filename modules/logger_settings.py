from loguru import logger

from config_data import config

logger.add(f'logs/{config.LOGGER.get("log_name")}.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='DEBUG', rotation=config.LOGGER.get("rotation"), compression='zip')
logger.add(f'logs/{config.LOGGER.get("log_name")}_error.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='ERROR', rotation=config.LOGGER.get("rotation"), compression='zip')
