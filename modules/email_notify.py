import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config_data import config, email_messages
from modules.logger_settings import logger


def get_local_ip() -> int:
    """Getting a local ipv4 address"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    ip_address = sock.getsockname()[0]
    sock.close()
    return ip_address


def attachment(filename: str) -> Optional[MIMEText]:
    """A function that attaches a file to the email"""
    try:
        with open(f'logs/{filename}', mode='r', encoding='utf-8') as file:
            att_part = MIMEText(file.read(), 'plain', 'utf-8')
            att_part.add_header('Content-Disposition', 'attachment', filename=filename)
        return att_part
    except FileNotFoundError:
        logger.error(f"File not found: {filename} in attachment func")
        return None


def send_email(status: str, result: list, error_msg: OSError) -> None:
    """
    A function that sends an email to the addresses specified in the configuration file.
    Without authorization.
    Args:
        status (str): Result of the function execution. Successful or error
        result (tuple): The result of performing compression (number of files, size, etc.)
        error_msg (OSError): Error message to be sent
    """

    try:
        if config.SMTP.get("enable"):
            subject, text, part = 'None', 'None', None
            host_ip = get_local_ip()
            if status == 'error':
                subject = "Compression execution error"
                text = email_messages.ERROR_TEXT.format(
                    path=config.COMPRESS.get('img_path'), files=result[0],
                    size=round(result[2], 2) if str(result[2]).isdigit() else 0,
                    time=result[3], ip=host_ip, error=error_msg
                )
                # list of files that we want to see attached to the mail
                logfile = config.LOGGER.get("log_name")
                log_file = f'{logfile}_error.log'
                part = attachment(filename=log_file)
            elif status == 'success':
                subject = "Compression completed successfully"
                text = email_messages.SUCCESS_TEXT.format(
                    path=config.COMPRESS.get('img_path'), files=result[1],
                    size=round(result[0], 2), time=result[2], ip=host_ip
                )
            # create a message object
            message = MIMEMultipart()
            message['From'] = config.SMTP.get("from_email")
            message['To'] = ', '.join(config.SMTP.get("to_email"))
            message['Subject'] = subject

            # add a text message to the email
            message.attach(MIMEText(text, 'plain', 'utf-8'))
            if part is not None:
                message.attach(part)

            # connecting to the email server
            with smtplib.SMTP(
                    host=config.SMTP.get("smtp_address"),
                    port=config.SMTP.get("smtp_port")
            ) as server:
                # server.login(user='login', password='pass') # uncomment if required
                # sending an email
                server.sendmail(
                    from_addr=message['From'],
                    to_addrs=config.SMTP.get("to_email"),
                    msg=message.as_string()
                )
    except smtplib.SMTPResponseException as smtp_err:
        error_code = smtp_err.smtp_code
        error_message = smtp_err.smtp_error
        logger.error(f'SMTP Error: {error_code} | {error_message}')
    except Exception as exc:
        logger.error(f'send_email func error: {exc}')
