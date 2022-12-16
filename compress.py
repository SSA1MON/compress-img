import os
from pathlib import Path
from time import time, sleep
from datetime import datetime
from loguru import logger
from config import img_path, app, postfix, creation_time, quality

logger.add("logs/compress.log", format="{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}", level="DEBUG",
           rotation="23:58", compression="zip")


@logger.catch
def creation_time_check(file_path: str) -> int:
    """
    Функция. Проверяет дату создания файла по полученному пути.

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
    Функция сжатия. Сжимает файлы-изображения в получаемой директории.

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

        # Игнорирует файлы с постфиксом в имени
        if postfix not in i:

            # Проверка, что время создания файла соответствует условию
            if not Path.is_dir(iter_path):
                file_date = creation_time_check(str(iter_path))
                if file_date < creation_time:
                    logger.info(f'>>> "{i}" doesn`t meet the requirement ({file_date}/{creation_time} days)')
                    continue

            # Поиск и замена пробелов в имени файлов
            if " " in i and not Path.exists(Path(path, i.replace(' ', '-'))):
                if Path.is_dir(iter_path) is not True:
                    new_filename = i.replace(' ', '-')
                    os.rename(src=iter_path, dst=str(Path(path, new_filename)))
                    logger.info(f'>>> "{i}" was renamed to "{new_filename}"')
                    i = new_filename
                    iter_path = Path(path, i)
                    renamed += 1

            # Рекурсивный проход по всем директориям внутри пути
            if Path.is_dir(iter_path):
                logger.info("Go to " + str(iter_path))
                res = images_compress(path=str(iter_path), renamed=renamed, compressed=compressed)
                renamed = res[0]
                compressed = res[1]
                logger.info("Back to " + str(path))

            # Сжатие изображения mozjpeg`ом
            elif Path.is_file(iter_path):
                exec_time = time()
                extension = i.index(i[- (i[::-1].find('.')) - 1:])  # Расширение файла в виде индекса
                new_filename = i[:extension] + postfix + i[extension:]
                logger.info(f"In the process of compression: {i}")
                print(f'"{Path(path, new_filename)}"')
                compress_res = os.system(
                    command=f'{app} -quality {quality} -outfile "{Path(path, new_filename)}" "{iter_path}"'
                )

                if compress_res == 0:
                    # Проверка на существование сжатого файла и удаление оригинала
                    if Path.exists(Path(path, new_filename)):
                        os.remove(path=iter_path)
                    exec_time = round(time() - exec_time, 2)
                    logger.info(f">>> {i} was compressed in {exec_time} seconds.")
                    compressed += 1
    return renamed, compressed


if __name__ == "__main__":
    logger.info('Starting script...')
    sleep(1)
    uptime = time()
    result = images_compress(path=img_path)
    uptime = round(time() - uptime, 2)
    # logger.info(f'Script finished. Renamed: {result[0]} Compressed: {result[1]} Time: {uptime} sec.')
