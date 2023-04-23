from time import monotonic
from loguru import logger

from config import config
from handlers import path_files_handler

logger.add(f'logs/{config["logger"]["log_name"]}.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='DEBUG', rotation=config["logger"]["rotation"], compression='zip')
logger.add(f'logs/{config["logger"]["log_name"]}_error.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='ERROR', rotation=config["logger"]["rotation"], compression='zip')


@logger.catch
def main() -> None:
    """ main function """
    logger.info('Starting script...')
    uptime = monotonic()
    result = path_files_handler(path=config["compress"]["img_path"])
    if None in result:
        logger.error('The storage is unavailable or something went wrong. Stopping...')
    uptime = round(monotonic() - uptime, 2)
    logger.success(f'Script finished. Compressed files: {result[1]}. '
                   f'Saved: {round(result[0], 2)} MB | Time: {uptime} seconds.')


if __name__ == '__main__':
    main()
