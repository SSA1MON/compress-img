import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Optional, Tuple, List
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PIL import Image
from loguru import logger
from wrapt_timeout_decorator import timeout


try:
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
except FileNotFoundError as error:
    print(error)
    sys.exit(0)


logger.add(f'logs/{config.get("logger").get("log_name")}.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='DEBUG', rotation=config.get("logger").get("rotation"), compression='zip')
logger.add(f'logs/{config.get("logger").get("log_name")}_error.log',
           format='{time:DD.MM.YYYY HH:mm:ss} | {level} | {message}',
           level='ERROR', rotation=config.get("logger").get("rotation"), compression='zip')


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
        thr.join(timeout=config.get("connection_timeout"))
        if thr.is_alive():
            return None
        return True
    except OSError as e:
        logger.error(f'Error: {e}')
        raise OSError(f'Error: {e}') from e


def send_email(error_msg: OSError) -> None:
    """
    A function that sends an email to the addresses specified in the configuration file.
    Without authorization.
    Args:
        error (OSError): The error message to be sent
    """

    def attachment(filename: str) -> MIMEApplication:
        """A function that attaches a file to the email"""
        try:
            with open(f'logs/{filename}', 'r', encoding='utf-8') as logs:
                part = MIMEApplication(logs.read())
                part.add_header(
                    'Content-Disposition', 'attachment',
                    filename=filename
                )
            return part
        except FileNotFoundError:
            logger.error(f"File not found: {filename} in attachment func (email_module.py)")

    if config["smtp"]["enable"]:
        # create a message object
        message = MIMEMultipart()
        message['Subject'] = 'Compression execution error'
        message['From'] = config["smtp"]["from_email"]
        message['To'] = ', '.join(config["smtp"]["to_email"])

        # add a text message to the email
        text = MIMEText(f'An error occurred while executing\n\n{error_msg}')
        message.attach(text)

        logfile = config.get("logger").get("log_name")
        files = [f'{logfile}.log', f'{logfile}_error.log']

        for i_name in files:
            part = attachment(i_name)
            if part is not None:
                message.attach(part)

        try:
            with smtplib.SMTP(
                    config.get("smtp").get("smtp_server"),
                    config.get("smtp").get("smtp_port")
            ) as server:
                server.sendmail(
                    message['From'],
                    config.get("smtp").get("to_email"),
                    message.as_string()
                )
        except smtplib.SMTPResponseException as smtp_err:
            error_code = smtp_err.smtp_code
            error_message = smtp_err.smtp_error
            logger.error(f"SMTP Error: {error_code} | {error_message}")


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
    img_formats = tuple(config["compress"]["image_formats"])
    # Removes all values with a postfix
    files_list = [filename for filename in os.listdir(path)
                  if config.get("compress").get("postfix") not in filename
                  and filename.lower().endswith(img_formats) or Path.is_dir(Path(path, filename))
                  ]
    files_list.sort()
    # Getting information about the file creation date and entering it into the dictionary
    days_list = {filename: creation_time_check(str(Path(path, filename)))
                 for filename in files_list}
    # Checking that the file creation time matches the condition
    files_list = [filename for filename, days in days_list.items()
                  if Path.is_file(Path(path, filename))
                  and days >= config.get("compress").get("creation_days") or Path.is_dir(Path(path, filename))
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
        for i_ext in config.get("compress").get("image_formats"):
            extension_index = name.rfind(i_ext)
            # Checking for the presence of a file extension in the received string
            if extension_index != -1:
                return extension_index
    return None


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


@timeout(config.get("execution_timeout"), use_signals=False)
def compress_image(
        dir_path: str, img_path: str, filename: str, ext_index: Optional[int]
) -> Tuple[int, float, OSError]:
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
    new_filename = filename[:ext_index] + config.get("compress").get("postfix") + filename[ext_index:]
    exec_time = monotonic()
    try:
        size = convert_size(os.path.getsize(img_path))
        logger.info(f'In the process of compression: {filename} [{size}MB]')
        with Image.open(img_path) as img:
            img.save(Path(dir_path, new_filename), quality=config.get("compress").get("quality"))
        size = size - convert_size(os.path.getsize(Path(dir_path, new_filename)))
        os.remove(img_path)
        exec_time = round(monotonic() - exec_time, 2)
        logger.info(f'>>> {filename} was compressed in {exec_time} seconds.')
        return 1, size
    except OSError as error:
        logger.error(f'>>> "{img_path}" could not be compressed. Error: {error}')
        return 0, 0


def path_files_handler(
        path: str, compressed_size: int = 0, compressed_img: int = 0
) -> Tuple:
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
                return compressed_size, compressed_img

            iter_path = Path(path, i_file_name)
            extension_index = search_extension_index(path=iter_path, name=i_file_name)

            # Recursive traversal of all directories inside the path and
            # ignoring the directories specified in the configuration
            if Path.is_dir(iter_path):
                if i_file_name in config.get("compress").get("ignore_directories") \
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
                    result = compress_image(
                        dir_path=path, img_path=str(iter_path),
                        filename=i_file_name, ext_index=extension_index
                    )
                    compressed_img += result[0]
                    compressed_size += result[1]
                except TimeoutError as e:
                    logger.error(f'Error: {e}')
                    continue
            else:
                logger.warning(f'This is not an image: {iter_path}')
        return compressed_size, compressed_img
    except OSError as err:
        logger.error(f'Error: {err}')
        return compressed_size, compressed_img, err


@logger.catch
def main() -> None:
    """ main function """
    logger.info('Starting script...')
    uptime = monotonic()
    result = path_files_handler(path=config.get("compress").get("img_path"))
    uptime = round(monotonic() - uptime, 2)
    final_message = f'Script finished. Compressed files: {result[1]}. ' \
                    f'Saved: {round(result[0], 2)} MB | Time: {uptime} seconds.'
    if len(result) > 2:
        logger.error('The storage is unavailable or something went wrong. Stopping...')
        logger.success(final_message)
        send_email(error_msg=result[-1])
    else:
        logger.success(final_message)


if __name__ == '__main__':
    main()
