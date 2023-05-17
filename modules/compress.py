import os
from pathlib import Path
from time import monotonic
from typing import Optional, Tuple

from PIL import Image
from wrapt_timeout_decorator import timeout

from config_data import config
from modules.logger_settings import logger


def convert_size(size: int) -> float:
    """
    Converts the size in bytes to the size in megabytes.
    Args:
        size (int): Size in bytes
    Returns:
        size (float): Size in megabytes
    """
    if size >= 105:     # bytes
        result = size / (1024 ** 2)
        return round(result, 2)
    return 0


@timeout(config.TIMEOUT.get("execution_timeout"), use_signals=False)
def compress_image(
        dir_path: str, img_path: str, filename: str, ext_index: Optional[int]
) -> Tuple[int, float]:
    """
    Compression function. Compresses the image files in the directory
    by the resulting path and renames the files by adding a postfix
    to the name. Also counts the difference in size and returns the result.
    Args:
        dir_path (str): Path to the directory with images
        img_path (str): Path to a specific image
        filename (str): File name
        ext_index (int): File extension index
    Returns:
        int: 1 if the compression was successful, 0 if not
        size (float): Saved size as a result of compression
    """
    new_filename = \
        filename[:ext_index] + config.COMPRESS.get("postfix") + filename[ext_index:]
    exec_time = monotonic()
    try:
        size = convert_size(os.path.getsize(img_path))
        logger.info(f'In the process of compression: {filename} [{size}MB]')
        with Image.open(img_path) as img:
            img.save(Path(dir_path, new_filename), quality=config.COMPRESS.get("quality"))
        size = size - convert_size(os.path.getsize(Path(dir_path, new_filename)))
        os.remove(img_path)
        exec_time = round(monotonic() - exec_time, 2)
        logger.info(f'>>> {filename} was compressed in {exec_time} seconds.')
        return 1, size
    except OSError as oserr:
        logger.error(f'>>> "{img_path}" could not be compressed. Error: {oserr}')
        return 0, 0
