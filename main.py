from time import monotonic

from config_data import config
from modules import email_notify
from modules.logger_settings import logger
from modules.search_files import path_files_handler


@logger.catch
def main() -> None:
    logger.info('Starting script...')
    uptime = monotonic()
    result = path_files_handler(path=config.COMPRESS.get("img_path"))
    uptime = round(monotonic() - uptime, 2)
    final_message = f'Script finished. Compressed files: {result[1]}. ' \
                    f'Saved: {round(result[0], 2)} MB | Time: {uptime} seconds.'
    if len(result) > 2:
        logger.error('The storage is unavailable or something went wrong. Stopping...')
        logger.success(final_message)
        email_status = ['error', result[-1]]
    else:
        logger.success(final_message)
        email_status = ['success', None]
    email_notify.send_email(
        status=email_status[0], result=result + [uptime], error_msg=email_status[1]
    )


if __name__ == '__main__':
    main()
