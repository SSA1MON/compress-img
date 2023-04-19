import json
import os
import threading

from pathlib import Path
from time import monotonic, sleep
from datetime import datetime
from typing import Optional, Tuple, List
from PIL import Image
from wrapt_timeout_decorator import timeout
from loguru import logger

with open('config.json', mode='r', encoding='utf-8') as file:
    config = json.load(file)

logger.add(f'logs/{config["log_name"]}.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='DEBUG', rotation=f'{config["rotation"]}', compression='zip')
logger.add(f'logs/{config["log_name"]}_error.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='ERROR', rotation=f'{config["rotation"]}', compression='zip')


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
        thr.join(timeout=config["connection_timeout"])
        if thr.is_alive():
            return None
        return True
    except OSError as err:
        logger.error(f'Error: {err}')
        raise OSError(f'Error: {err}') from err


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
    img_formats = tuple(config["image_formats"])
    # Removes all values with a postfix
    files_list = [filename for filename in os.listdir(path)
                  if config["postfix"] not in filename
                  and filename.lower().endswith(img_formats) or Path.is_dir(Path(path, filename))
                  ]
    files_list.sort()
    # Getting information about the file creation date and entering it into the dictionary
    days_list = {filename: creation_time_check(str(Path(path, filename)))
                 for filename in files_list}
    # Checking that the file creation time matches the condition
    files_list = [filename for filename, days in days_list.items()
                  if Path.is_file(Path(path, filename))
                  and days >= config["creation_days"] or Path.is_dir(Path(path, filename))
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
        for i_ext in config["image_formats"]:
            extension_index = name.rfind(i_ext)
            # Checking for the presence of a file extension in the received string
            if extension_index != -1:
                return extension_index
    return None


def convert_size(size: int) -> int:
    """
    Converts the size in bytes to the size in megabytes.
    Args:
        size (int): Size in bytes
    Returns:
        size (int): Size in megabytes
    """
    if size >= 105:     # bytes
        result = size / (1024 ** 2)
        return round(result, 2)
    return 0


@timeout(config["execution_timeout"], use_signals=False)
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
    new_filename = filename[:ext_index] + config["postfix"] + filename[ext_index:]
    exec_time = monotonic()
    try:
        size = convert_size(os.path.getsize(img_path))
        logger.info(f'In the process of compression: {filename} [{size}MB]')
        with Image.open(img_path) as img:
            img.save(Path(dir_path, new_filename), quality=config["quality"])
        size = round(size - convert_size(os.path.getsize(Path(dir_path, new_filename))), 2)
        os.remove(img_path)
        exec_time = round(monotonic() - exec_time, 2)
        logger.info(f'>>> {filename} was compressed in {exec_time} seconds.')
        return 1, size
    except OSError as error:
        logger.error(f'>>> "{img_path}" could not be compressed. Error: {error}')
        return 0, 0


def path_files_handler(
        path: str, compressed_size: int = 0, compressed_img: int = 0
) -> Optional[Tuple]:
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
        None: If the files were not found or something went wrong
    """
    logger.info(f'Current directory: {path}')
    try:
        files_list = get_files_list(path=path)
        for i_file_name in files_list:
            # Checking the connection to the directory
            available_path = timeout_connect(path=path)
            if not available_path:
                logger.error('Path is unavailable (timeout). Interruption...')
                return compressed_size, compressed_img

            iter_path = Path(path, i_file_name)
            extension_index = search_extension_index(path=iter_path, name=i_file_name)

            # Recursive traversal of all directories inside the path and
            # ignoring the directories specified in the configuration
            if Path.is_dir(iter_path):
                if i_file_name in config["ignore_directories"] or i_file_name.startswith('.'):
                    logger.info(f'>>> "{i_file_name}" dir is ignored.')
                    continue
                logger.info(f'Going to {iter_path}')
                res = path_files_handler(
                    path=str(iter_path), compressed_size=compressed_size,
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
                    result = compress_image(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, ext_index=extension_index
                    )
                    compressed_img += result[0]
                    compressed_size += result[1]
                except TimeoutError as err:
                    logger.error(f'Error: {err}')
                    continue
            else:
                logger.warning(f'This is not an image: {iter_path}')
        return compressed_size, compressed_img
    except OSError as err:
        logger.error(f'Error: {err}')
        return compressed_size, compressed_img, None


@logger.catch
def main() -> None:
    """ main function """
    logger.info('Starting script...')
    sleep(1)
    uptime = monotonic()
    result = path_files_handler(path=config["img_path"])
    if None in result:
        logger.error('The storage is unavailable or something went wrong. Stopping...')
    uptime = round(monotonic() - uptime, 2)
    logger.success(f'Script finished. Compressed files: {result[1]}. '
                   f'Saved: {result[0]} MB | Time: {uptime} seconds.')


if __name__ == '__main__':
    main()
