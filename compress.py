import os
import concurrent.futures
import config as cfg

from pathlib import Path
from time import monotonic
from datetime import datetime
from loguru import logger
from typing import Optional

logger.add(f"logs/{cfg.log_name}.log", format="{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}", level="DEBUG",
           rotation="1 day", compression="zip")
logger.add(f"logs/{cfg.log_name}_error.log", format="{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}", level="ERROR",
           rotation="1 day", compression="zip")


@logger.catch
def timeout(path: Path, pool: concurrent.futures.ThreadPoolExecutor) -> Optional[list]:
    """
    Function that tracks time to connect to the received directory

    Parameters:
        path (Path): Path to the directory or file.
        pool (concurrent.futures.ThreadPoolExecutor): Threads for async execution.
    Returns:
        future.result (list): A list containing the names of directories and/or files.
    """

    future = pool.submit(os.listdir, path)
    try:
        return future.result(cfg.timeout_time)
    except concurrent.futures.TimeoutError:
        return None


@logger.catch
def creation_time_check(file_path: Path) -> int:
    """
    Function of checking creation date. Checks the creation date of the file from the received path.

    Parameters:
        file_path (Path): Path to the directory or file.
    Returns:
        res (int): Number of days elapsed from the current time to the date of file creation.
    """

    current_time = datetime.now()
    create_time = datetime.fromtimestamp(os.path.getctime(file_path))
    res = str(current_time - create_time)
    if "days" in res:
        res = int(res.split()[0])
    else:
        res = 0
    return res


@logger.catch
def images_compress(path: Path, renamed: int = 0, compressed: int = 0) -> tuple[int, int]:
    """
    Compression function. Compresses image files in all nested directories from the received path.

    Parameters:
        path (Path): Path to the directory or file.
        renamed (int): Variable for counting the number of renamed files.
        compressed (int): Variable for counting the number of compressed files.
    Returns:
        renamed (int): Number of renamed files.
        compressed (int): Number of compressed files.
    """

    short_path = str(path)[str(path).find(Path.cwd().stem):]
    logger.info(f"Current directory \"{short_path}\"")

    # Checking connection to the directory
    pool = concurrent.futures.ThreadPoolExecutor()
    available_path = timeout(path=path, pool=pool)

    if available_path is not None:
        for i in available_path:
            iter_path = Path(path, i)
            extension = i.index(i[-(i[::-1].find(".")) - 1:])  # File extension index

            # Checking for a directory and ignoring files with a postfix in the name
            if Path.exists(iter_path) and cfg.postfix not in i:
                # Recursive traversal through all directories inside the path
                if Path.is_dir(iter_path):
                    logger.info(f"Going to \"{short_path}\"")
                    res = images_compress(path=iter_path, renamed=renamed, compressed=compressed)
                    renamed, compressed = res[0], res[1]
                    logger.info(f"Back to \"{short_path}\"")
                    continue

                # Checking that the object is a file and has the specified extensions in the name
                if not Path.is_dir(iter_path) and i[extension:] in cfg.image_format:
                    file_date = creation_time_check(iter_path)
                    new_filename = i.replace(" ", "-")

                    # Checking that the file creation time matches condition
                    if file_date < cfg.creation_time:
                        logger.info(f"  \"{i}\" does not meet the condition ({file_date}/{cfg.creation_time} days)")
                        continue

                    # Finding and replacing spaces in the file name
                    if " " in i and not Path.exists(Path(path, new_filename)):
                        os.rename(src=iter_path, dst=Path(path, new_filename))
                        logger.info(f"  \"{i}\" was renamed to \"{new_filename}\"")
                        i = new_filename
                        iter_path = Path(path, i)
                        renamed += 1

                    # File compression using mozjpeg
                    exec_time = monotonic()
                    new_filename = i[:extension] + cfg.postfix + i[extension:]
                    logger.info(f"In the process of compression: {i}")
                    os.system(
                        command=f"{cfg.app} -quality {cfg.quality} -progressive "
                                f"-outfile \"{Path(path, new_filename)}\" \"{iter_path}\""
                    )

                    # Checking for the existence of a compressed file and deleting the original
                    if Path.exists(Path(path, new_filename)):
                        os.remove(path=iter_path)
                        exec_time = round(monotonic() - exec_time, 2)
                        logger.info(f"  {i} was compressed in {exec_time} seconds.")
                        compressed += 1
                else:
                    logger.warning(f"This is not an image: {Path(short_path, i)}")
            else:
                logger.warning(f"Wrong name or path does not exist: {Path(short_path, i)}")
        return renamed, compressed
    else:
        logger.error(f"Path \"{short_path}\" is unavailable (timeout {cfg.timeout_time} sec). Break...")
        return renamed, compressed


if __name__ == "__main__":
    try:
        logger.info("Starting script...")
        uptime = monotonic()
        result = images_compress(path=cfg.img_path)
        uptime = round(monotonic() - uptime, 2)
        logger.success(f"Script finished. Renamed: {result[0]} Compressed: {result[1]} Time: {uptime} sec.")
    except Exception as ex:
        logger.critical(ex)
