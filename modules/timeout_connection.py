import os
import threading
from pathlib import Path
from typing import Optional

from config_data import config
from modules.logger_settings import logger


def timeout_connect(path: str) -> Optional[bool]:
    """
    The function checks the availability of the received path.
    Returns None if Path has not responded after the specified amount of time.
    Args:
        path (str): Path to the directory
    Returns:
        contents (list): List with file names
    """
    try:
        if not Path.exists(Path(path)):
            logger.error(f'>>> "{path}" does not exist.')
            raise FileNotFoundError(f'>>> "{path}" does not exist.')
        contents = []
        thr = threading.Thread(target=lambda: contents.extend(os.listdir(path)))
        thr.daemon = True
        thr.start()
        thr.join(timeout=config.TIMEOUT.get("connection_timeout"))
        if thr.is_alive():
            return None
        return True
    except OSError as oserr:
        logger.error(f'Error: {oserr}')
        raise OSError(f'Error: {oserr}') from oserr
