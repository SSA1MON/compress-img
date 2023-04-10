import json
import os
import sys
import re
import threading

from pathlib import Path
from time import monotonic, sleep
from datetime import datetime
from PIL import Image
from typing import Optional, Tuple
from loguru import logger

with open('config.json', mode='r', encoding='utf-8') as file:
    config = json.load(file)

logger.add(f'logs/{config["log_name"]}.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='DEBUG', rotation=f'{config["rotation"]}', compression='zip')
logger.add(f'logs/{config["log_name"]}_error.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='ERROR', rotation=f'{config["rotation"]}', compression='zip')


def timeout(path: str) -> Optional[list]:
    """
    The function checks the availability of the received path.
    Returns None if Path has not responded after the specified amount of time.
    Args:
        path (str): Path to the directory
    Returns:
        contents (list): List with file names
    """
    if not Path.exists(Path(path)):
        logger.error(f'>>> "{path}" does not exist.')
        raise FileNotFoundError(f'>>> "{path}" does not exist.')
    contents = []
    thr = threading.Thread(target=lambda: contents.extend(os.listdir(path)))
    thr.daemon = True
    thr.start()
    thr.join(timeout=config["timeout_time"])
    if thr.is_alive():
        return None
    return contents


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


def search_extension_index(name: str) -> Optional[int]:
    """
    Function to search for the file extension from the received string.
    Args:
        name (str): File name
    Returns:
        extension_index (int): The index of the start of the file extension in the file name string
    """
    name = name.lower()
    for i_ext in config["image_format"]:
        extension_index = name.rfind(i_ext)
        # Checking for the presence of a file extension in the received string
        if extension_index != -1:
            return extension_index
    return None


def search_filename_spaces(
        dir_path: str, img_path: str, filename: str, new_filename: str
) -> bool:
    """
    The function searches for the space character in the file name and replaces it.
    Args:
        dir_path (str): Path to the directory with images
        img_path (str): Path to a specific image
        filename (str): File name
        new_filename (str): New file name
    Returns:
        bool: True if the search was successful
    """
    try:
        if ' ' in filename and not Path.exists(Path(dir_path, new_filename)):
            os.rename(src=img_path, dst=str(Path(dir_path, new_filename)))
            logger.info(f'>>> "{filename}" was renamed to "{new_filename}"')
            return True
        return False
    except OSError as error:
        logger.error(f'>>> "{img_path}" could not be renamed. Error: {error}')
        return False


def compress_image(dir_path: str, img_path: str, filename: str, ext_index: Optional[int]) -> int:
    """
    Compression function. Compresses image files in the directory by the received path
    and rename the file depending on the config.
    Args:
        dir_path (str): Path to the directory with images
        img_path (str): Path to a specific image
        filename (str): File name
        ext_index (int): File extension index
    Returns:
        int: 1 if the compression was successful, 0 if not
    """
    new_filename = filename[:ext_index] + config["postfix"] + filename[ext_index:]
    logger.info(f'In the process of compression: {filename}')
    exec_time = monotonic()
    try:
        img = Image.open(img_path)
        img.save(Path(dir_path, new_filename), quality=config["quality"])
        img.close()
        os.remove(img_path)
        exec_time = round(monotonic() - exec_time, 2)
        logger.info(f'>>> {filename} was compressed in {exec_time} seconds.')
        return 1
    except OSError as error:
        logger.error(f'>>> "{img_path}" could not be compressed. Error: {error}')
        return 0


def path_files_handler(
        path: str,
        renamed: int = 0,
        compressed: int = 0,
        warn_count: int = 0
) -> Optional[Tuple]:
    """
    A recursive function that searches for images inside all directories by the resulting path.
    Passes the found path to the compression function.
    Args:
        path (str): Path to the directory
        renamed (int): Variable for counting the number of renamed files
        compressed (int): Variable for counting the number of compressed files
        warn_count (int): Variable for counting the number of warnings in a row
    Returns:
        renamed (int): Number of renamed files
        compressed (int): Number of compressed files
        None: If the files were not found or something went wrong
    """
    logger.info(f'Current directory: {path}')
    try:
        # Checking the connection to the directory
        available_path = timeout(path=path)
        if available_path is None:
            logger.error('Path is unavailable (timeout). Interruption...')
            return renamed, compressed

        for i_file_name in os.listdir(path=path):
            iter_path = Path(path, i_file_name)
            extension_index = search_extension_index(name=i_file_name)

            # Checking for a directory and ignoring files with a postfix in the name
            if Path.exists(iter_path) and config["postfix"] not in i_file_name:

                # Recursive traversal of all directories inside the path and
                # ignoring the directories specified in the configuration
                if Path.is_dir(iter_path):
                    if i_file_name in config["ignore_directories"]:
                        logger.info(f'>>> "{i_file_name}" dir is ignored.')
                        continue

                    logger.info(f'Going to {iter_path}')
                    res = path_files_handler(
                        path=str(iter_path), renamed=renamed,
                        compressed=compressed, warn_count=warn_count
                    )
                    if res is None:
                        if warn_count >= config["max_warnings"]:
                            return None
                        logger.warning(f'>>> "{i_file_name}" was not found.')
                        continue
                    renamed, compressed = res[0], res[1]
                    logger.info(f'Back to {path}')
                    continue

                # Checking that the object is a file
                # and has the specified extensions in its name
                if not Path.is_dir(iter_path) and \
                        i_file_name[extension_index:].lower() in config["image_format"]:
                    timeout(path=path)
                    file_date = creation_time_check(str(iter_path))
                    new_filename = re.sub(r'\s', '-', i_file_name)

                    # Checking that the file creation time matches the condition
                    if file_date < config["creation_days"]:
                        logger.info(f'>>> "{i_file_name}" does not meet the condition '
                                    f'({file_date}/{config["creation_days"]} days)')
                        continue

                    # Finding and replacing spaces in the file name
                    # and the absence of such a path
                    space_result = search_filename_spaces(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, new_filename=new_filename
                    )
                    if space_result:
                        i_file_name = new_filename
                        iter_path = Path(path, i_file_name)
                        renamed += 1

                    # File compression by pillow
                    result = compress_image(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, ext_index=extension_index
                    )
                    compressed += result
                else:
                    logger.warning(f'This is not an image: {iter_path}')
            else:
                logger.warning(f'Wrong name or path does not exist: {iter_path}')
                if not Path.exists(iter_path):
                    warn_count += 1
                if warn_count >= config["max_warnings"]:
                    logger.error('Maximum number of warnings reached. '
                                 'Something\'s wrong. Stopping...')
                    sys.exit(0)
        return renamed, compressed, warn_count
    except OSError as error:
        logger.error(f'Error: {error}')
        return None


@logger.catch
def main() -> None:
    logger.info('Starting script...')
    sleep(1)
    uptime = monotonic()
    result = path_files_handler(path=config["img_path"])
    if result is None:
        logger.critical('The storage is unavailable or something went wrong. Stopping...')
        sys.exit(1)
    uptime = round(monotonic() - uptime, 2)
    logger.success(f'Script finished. Renamed: {result[0]} '
                   f'| Compressed: {result[1]} | Time: {uptime} seconds.')


if __name__ == '__main__':
    main()
