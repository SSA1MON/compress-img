import os
from sys import stdout
from pathlib import Path
from time import time, sleep
from datetime import datetime
from config import img_path, app, postfix, creation_time, quality


def standby_func(secs: int) -> None:
    """
    Функция ожидания. Ожидает указанное количество времени в секундах с
    динамичным выводом в терминал.

    Parameters:
        secs (int): Количество секунд для ожидания.
    Returns:
        None
    """

    for i in range(secs, -1, -1):
        sleep(1)
        stdout.write(f'\rWaiting [{i}] sec...')
        stdout.flush()
    print()


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
    res = int(str(current_time - create_time)[0])
    return res


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

    for i in os.listdir(path=path):
        # Checking that the file creation time fits the condition
        iter_path = Path(path, i)
        file_date = creation_time_check(str(iter_path))
        if file_date < creation_time:
            print(f'>>> "{i}" doesn`t meet the requirement ({file_date}/{creation_time} days).')
            continue

        #   Finding spaces in filename and deleting them
        if " " in i and not Path.exists(Path(path, i.replace(' ', '_'))):
            os.rename(src=iter_path, dst=str(Path(path, i.replace(' ', '_'))))
            new_name = i.replace(' ', '_')
            print(f'>>> "{i}" was renamed to "{new_name}"')
            i = new_name
            iter_path = Path(path, i)
            renamed += 1

        # Recursive running all directories in path
        if Path.is_dir(Path(path, i)):
            print("\nGo to " + str(iter_path))
            res = images_compress(path=str(iter_path), renamed=renamed, compressed=compressed)
            renamed = res[0]
            compressed = res[1]
            print("Back to " + str(path))

        #   Compress images by mozjpeg ignore files with '_compressed' in name
        elif Path.is_file(iter_path) and postfix not in i:
            exec_time = time()
            extension = i.find('.')
            print(f"In the process of compression: {i}")
            os.system(command=f"{app} -quality {quality} "
                              f"-outfile {Path(path, i[:extension] + postfix + i[extension:])} {iter_path}")

            # Check for the existing compressed file and deleting original
            if Path.exists(Path(path, i[:extension] + postfix + i[extension:])):
                os.remove(path=iter_path)

            exec_time = round(time() - exec_time, 2)
            print(f">>> {i} was compressed in {exec_time} seconds.")
            compressed += 1
    return renamed, compressed


if __name__ == "__main__":
    print('Starting script...')
    standby_func(secs=1)
    uptime = time()
    result = images_compress(path=img_path)
    uptime = round(time() - uptime, 2)
    if result is not None:
        print('\nScript ended. Renamed:', result[0], 'Compressed:', result[1], "Time:", uptime, "sec.")
    standby_func(secs=3)
