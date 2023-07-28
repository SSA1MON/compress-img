import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from config_data import config
from modules import compress
from modules.logger_settings import logger
from modules.timeout_connection import timeout_connect


def get_files_list(path: str) -> List[str]:
    """
    The function gets a list of files by the received path and generates
    a list of file names according to the following conditions: there is
    no postfix in the file name, created no earlier than specified in
    the configuration file. Also sorts the values in the list.
    Args:
        path (str): Path to the directory
    Returns:
        files_list (list): List with file names
    """
    img_formats = tuple(config.COMPRESS.get("image_formats"))
    # Removes all values with a postfix
    files_list = [filename for filename in os.listdir(path)
                  if (config.COMPRESS.get("postfix") not in filename
                      and filename.lower().endswith(img_formats)
                      and not Path.is_dir(Path(path, filename)))
                  ]
    files_list.sort()
    # Getting information about the file creation date and entering it into the dictionary
    days_list = {filename: creation_time_check(str(Path(path, filename)))
                 for filename in files_list}
    # Checking that the file creation time matches the condition
    files_list = [filename for filename, days in days_list.items()
                  if (Path.is_file(Path(path, filename))
                      and days >= config.COMPRESS.get("creation_days"))
                  or Path.is_dir(Path(path, filename))
                  ]
    return files_list


def creation_time_check(file_path: str) -> int:
    """
    The function of checking the creation date. Checks the file creation date by the received path.
    Args:
        file_path (str): Path to the file
    Returns:
        res (int): The number of days elapsed from the current time to the date of file creation.
    """
    current_time = datetime.now()
    create_time = datetime.fromtimestamp(os.path.getctime(file_path))
    res = current_time - create_time
    if 'days' in str(res):
        res = res.days  # type: ignore
    else:
        res = 0  # type: ignore[assignment]
    return res  # type: ignore


def search_extension_index(path: Path, name: str) -> Optional[int]:
    """
    Function to search for the file extension from the received string.
    Args:
        path (Path): Path to the directory
        name (str): File name
    Returns:
        extension_index (int): The index of the start of the file extension in the file name string
    """
    if not Path.is_dir(path):
        name = name.lower()
        for i_ext in config.COMPRESS.get("image_formats"):
            extension_index = name.rfind(i_ext)
            # Checking for the presence of a file extension in the received string
            if extension_index != -1:
                return extension_index
    return None


def path_files_handler(
        path: str, compressed_size: int = 0, compressed_img: int = 0
) -> List:
    """
    A recursive function that searches for images inside all directories by the resulting path.
    Passes the found path to the compression function.
    Args:
        path (str): Path to the directory
        compressed_size (int): Variable for calculating the total compressed size
        compressed_img (int): Variable for counting the number of compressed files
    Returns:
        compressed_size (int): Total size of the compressed size
        compressed_img (int): Number of compressed files
        err (OSError): Error object if the path is unavailable
    """
    logger.info(f'Current directory: {path}')
    try:
        files_list = get_files_list(path=path)
        for i_file_name in files_list:
            # Checking the connection to the directory
            available_path = timeout_connect(path=path)
            if not available_path:
                logger.error('Path is unavailable (timeout). Interruption...')
                return [compressed_size, compressed_img]

            iter_path = Path(path, i_file_name)
            extension_index = search_extension_index(path=iter_path, name=i_file_name)

            # Recursive traversal of all directories inside the path and
            # ignoring the directories specified in the configuration
            if Path.is_dir(iter_path):
                if i_file_name in config.COMPRESS.get("ignore_directories") \
                        or i_file_name.startswith('.'):
                    logger.info(f'>>> "{i_file_name}" dir is ignored.')
                    continue
                logger.info(f'Going to {iter_path}')
                res = path_files_handler(
                    path=str(iter_path),
                    compressed_size=compressed_size,
                    compressed_img=compressed_img
                )
                if res is not None:
                    compressed_size, compressed_img = res[0], res[1]
                logger.info(f'Back to {path}')
                continue

            # Checking that the object is a file
            # and has the specified extensions in its name
            if not Path.is_dir(iter_path):
                timeout_connect(path=path)

                # File compression by pillow
                try:
                    result = compress.compress_image(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, ext_index=extension_index
                    )
                    compressed_img += result[0]
                    compressed_size += result[1]
                except TimeoutError as errtime:
                    logger.error(f'Error: {errtime}')
                    continue
            else:
                logger.warning(f'This is not an image: {iter_path}')
        return [compressed_size, compressed_img]
    except OSError as err:
        logger.error(f'Error: {err}')
        return [compressed_size, compressed_img, str(err)]
