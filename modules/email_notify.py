import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config_data import config
from modules.logger_settings import logger


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


def send_email(status: str, result: str, error_msg: OSError) -> None:
    """
    A function that sends an email to the addresses specified in the configuration file.
    Without authorization.
    Args:
        status (str): Result of the function execution. Successful or error
        result (str): The result of performing compression (number of files, size, etc.)
        error_msg (OSError): Error message to be sent
    """
    try:
        if config.SMTP.get("enable"):
            subject, text = 'None', 'None'
            if status == 'error':
                subject = 'Compression execution error'
                text = f'{error_msg}\n\n{result}\n\n' \
                       'Notifications can be turned off in the config file'
            elif status == 'success':
                subject = 'Compression completed successfully'
                text = f'{result}\n\nNotifications can be turned off in the config file'
            # create a message object
            message = MIMEMultipart()
            message['From'] = config.SMTP.get("from_email")
            message['To'] = ', '.join(config.SMTP.get("to_email"))
            message['Subject'] = subject

            # add a text message to the email
            message.attach(MIMEText(text, 'plain', 'utf-8'))

            # list of files that we want to see attached to the mail
            logfile = config.LOGGER.get("log_name")
            files = [f'{logfile}.log', f'{logfile}_error.log']

            for i_name in files:
                part = attachment(filename=i_name)
                if part is not None:
                    message.attach(part)

            with smtplib.SMTP(
                    config.SMTP.get("smtp_address"),
                    config.SMTP.get("smtp_port")
            ) as server:
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
