import json
import os
import threading

from pathlib import Path
from time import monotonic, sleep
from datetime import datetime
from loguru import logger
from typing import Optional, Tuple

with open('config.json', mode='r', encoding='utf-8') as file:
    config = json.load(file)

logger.add(f'logs/{config["log_name"]}.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='DEBUG', rotation='1 day', compression='zip')
logger.add(f'logs/{config["log_name"]}_error.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='ERROR', rotation='1 day', compression='zip')


@logger.catch
def timeout(path: str) -> Optional[list]:
    """
    The function checks the availability of the received path.
    Returns None if the path has not responded after the specified amount of time.
    Args:
        path (str):
    Returns:
        contents (list):
    """
    contents = []
    thr = threading.Thread(target=lambda: contents.extend(os.listdir(path)))
    thr.daemon = True
    thr.start()
    thr.join(timeout=config["timeout_time"])
    if thr.is_alive():
        return None
    return contents


@logger.catch
def creation_time_check(file_path: str) -> int:
    """
    The function of checking the creation date. Checks the file creation date by the received path.
    Args:
        file_path (str): The path to the file
    Returns:
        res (int): The number of days elapsed from the current time to the date of file creation.
    """
    current_time = datetime.now()
    create_time = datetime.fromtimestamp(os.path.getctime(file_path))
    res = str(current_time - create_time)
    if 'days' in res:
        res = int(res.split()[0])
    else:
        res = 0
    return res


@logger.catch
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


@logger.catch
def search_filename_spaces(
        dir_path: str, img_path: str, filename: str, new_filename: str
) -> Optional[bool]:
    """
    The function searches for the space character in the file name and replaces it.
    Args:
        dir_path (str): Path to the directory with images
        img_path (str): The path to a specific image
        filename (str): File name
        new_filename (str): New file name
    Returns:
        bool: True if the search was successful
    """
    if ' ' in filename and not Path.exists(Path(dir_path, new_filename)):
        os.rename(src=img_path, dst=str(Path(dir_path, new_filename)))
        logger.info(f'>>> "{filename}" was renamed to "{new_filename}"')
        return True
    return False


@logger.catch
def compress_image(dir_path: str, img_path: str, filename: str, ext_index: Optional[int]) -> None:
    """
    Compression function. Compresses image files in the directory by the received path
    and rename the file depending on the config.
    Args:
        dir_path (str): Path to the directory with images
        img_path (str): The path to a specific image
        filename (str): File name
        ext_index (int): File extension index
    """
    new_filename = filename[:ext_index] + config["postfix"] + filename[ext_index:]
    logger.info(f'In the process of compression: {filename}')
    os.system(
        command=f'{Path(Path.cwd(), "mozjpeg/cjpeg")} -quality {config["quality"]} '
                f'-progressive -outfile "{Path(dir_path, new_filename)}" "{img_path}"'
    )


@logger.catch
def search_files(path: str, renamed: int = 0, compressed: int = 0) -> Tuple[int, int]:
    """
    A recursive function that searches for images inside all directories by the resulting path.
    Passes the found path to the compression function.
    Args:
        path (str): Path to the directory
        renamed (int): Variable for counting the number of renamed files
        compressed (int): Variable for counting the number of compressed files
    Returns:
        renamed (int): Number of renamed files
        compressed (int): Number of compressed files
    """
    logger.info(f'Current directory: {path}')
    available_path = timeout(path=path)

    # Checking the connection to the directory
    if available_path is not None:
        for i_file_name in os.listdir(path=path):
            iter_path = Path(path, i_file_name)
            extension_index = search_extension_index(name=i_file_name)

            # Checking for a directory and ignoring files with a postfix in the name
            if Path.exists(iter_path) and config["postfix"] not in i_file_name:
                # Recursive traversal through all directories inside the path
                if Path.is_dir(iter_path):
                    logger.info(f'Going to {iter_path}')
                    res = search_files(path=str(iter_path), renamed=renamed, compressed=compressed)
                    renamed, compressed = res[0], res[1]
                    logger.info(f'Back to {path}')
                    continue

                # Checking that the object is a file and has the specified extensions in its name
                if not Path.is_dir(iter_path) and \
                        i_file_name[extension_index:].lower() in config["image_format"]:
                    file_date = creation_time_check(str(iter_path))
                    new_filename = i_file_name.replace(' ', '-')

                    # Checking that the file creation time matches the condition
                    if file_date < config["creation_time"]:
                        logger.info(f'>>> "{i_file_name}" does not meet the condition '
                                    f'({file_date}/{config["creation_time"]} days)')
                        continue

                    # Finding and replacing spaces in the file name and the absence of such a path
                    space_result = search_filename_spaces(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, new_filename=new_filename
                    )
                    if space_result is True:
                        i_file_name = new_filename
                        iter_path = Path(path, i_file_name)
                        renamed += 1

                    # File compression using mozjpeg
                    exec_time = monotonic()
                    compress_image(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, ext_index=extension_index
                    )

                    # Checking for the existence of a compressed file and deleting the original
                    if Path.exists(Path(path, new_filename)):
                        os.remove(path=iter_path)
                        exec_time = round(monotonic() - exec_time, 2)
                        logger.info(f'>>> {i_file_name} was compressed in {exec_time} seconds.')
                        compressed += 1
                else:
                    logger.warning(f'This is not an image: {iter_path}')
            else:
                logger.warning(f'Wrong name or path does not exist: {iter_path}')
        return renamed, compressed
    else:
        logger.error('The path is unavailable (timeout). Interruption...')
        return renamed, compressed


def main():
    try:
        logger.info('Starting script...')
        sleep(1)
        uptime = monotonic()
        result = search_files(path=config["img_path"])
        uptime = round(monotonic() - uptime, 2)
        logger.success(f'Script finished. Renamed: {result[0]} '
                       f'| Compressed: {result[1]} | Time: {uptime} sec.')
    except Exception as ex:
        logger.critical(ex)


if __name__ == '__main__':
    main()
