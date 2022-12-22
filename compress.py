import os
from pathlib import Path
from time import time, sleep
from datetime import datetime
from loguru import logger
from config import img_path, app, postfix, creation_time, quality, image_format, log_name

logger.add(f"logs/{log_name}.log", format="{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}", level="DEBUG",
           rotation="1 day", compression="zip")


@logger.catch
def creation_time_check(file_path: str) -> int:
    """
    Функция проверки даты создания. Проверяет дату создания файла по полученному пути.

    Parameters:
        file_path (str): Путь к файлу.
    Returns:
        res (int): Количество прошедших дней от текущего времени до даты создания файла.
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
def images_compress(path: str, renamed: int = 0, compressed: int = 0) -> tuple[int, int]:
    """
    Функция сжатия. Сжимает файлы-изображения во всех вложенных директориях из полученного пути.

    Parameters:
        path (str): Путь до директории.
        renamed (int): Переменная для подсчета количества переименованных файлов.
        compressed (int): Переменная для подсчета количества сжатых файлов.
    Returns:
        renamed (int): Количество переименованных файлов.
        compressed (int): Количество сжатых файлов.
    """

    logger.info("Current directory: " + str(path))

    for i in os.listdir(path=path):
        iter_path = Path(path, i)
        extension = i.index(i[- (i[::-1].find('.')) - 1:])  # Расширение файла в виде индекса

        # Проверка наличия директории и игнорирование файлов с постфиксом в имени
        if Path.exists(iter_path) and postfix not in i:
            # Рекурсивный проход по всем директориям внутри пути
            if Path.is_dir(iter_path):
                logger.info("Going to " + str(iter_path))
                res = images_compress(path=str(iter_path), renamed=renamed, compressed=compressed)
                renamed, compressed = res[0], res[1]
                logger.info("Back to " + str(path))
                continue

            # Проверка, что объект - файл и имеет заданные расширения в своем имени
            if not Path.is_dir(iter_path) and i[extension:] in image_format:
                file_date = creation_time_check(str(iter_path))

                # Проверка, что время создания файла соответствует условию
                if file_date < creation_time:
                    logger.info(f'>>> "{i}" does not meet the condition ({file_date}/{creation_time} days)')
                    continue

                # Поиск и замена пробелов в имени файла
                if not Path.is_dir(iter_path) and ' ' in i and not Path.exists(Path(path, i.replace(' ', '-'))):
                    new_filename = i.replace(' ', '-')
                    os.rename(src=iter_path, dst=str(Path(path, new_filename)))
                    logger.info(f'>>> "{i}" was renamed to "{new_filename}"')
                    i = new_filename
                    iter_path = Path(path, i)
                    renamed += 1

                # Сжатие файла mozjpeg`ом
                exec_time = time()
                new_filename = i[:extension] + postfix + i[extension:]
                logger.info(f"In the process of compression: {i}")
                os.system(
                    command=f'{app} -quality {quality} -progressive -outfile "{Path(path, new_filename)}" "{iter_path}"'
                )

                # Проверка на существование сжатого файла и удаление оригинала
                if Path.exists(Path(path, new_filename)):
                    os.remove(path=iter_path)
                    exec_time = round(time() - exec_time, 2)
                    logger.info(f">>> {i} was compressed in {exec_time} seconds.")
                    compressed += 1
            else:
                logger.warning("This is not an image: " + str(iter_path))
        else:
            logger.warning("Wrong name or path does not exist: " + str(iter_path))
    return renamed, compressed


if __name__ == "__main__":
    try:
        logger.info('Starting script...')
        sleep(1)
        uptime = time()
        result = images_compress(path=img_path)
        uptime = round(time() - uptime, 2)
        logger.success(f'Script finished. Renamed: {result[0]} Compressed: {result[1]} Time: {uptime} sec.')
    except Exception as ex:
        logger.critical(ex)
