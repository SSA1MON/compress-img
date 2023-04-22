import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from loguru import logger

from main import config

# create a message object
message = MIMEMultipart()
message['Subject'] = 'Compression execution error'
message['From'] = config["smtp"]["from_email"]
message['To'] = ', '.join(config["smtp"]["to_email"])


def attachment(filename: str) -> MIMEApplication:
    """A function that attaches a file to the email"""
    try:
        with open(f'logs/{filename}', 'r', encoding='utf-8') as file:
            part = MIMEApplication(file.read())
            part.add_header(
                'Content-Disposition', 'attachment',
                filename=filename
            )
        return part
    except FileNotFoundError:
        logger.error(f"File not found: {filename} in attachment func (email_module.py)")


def send_email(error: OSError) -> None:
    """
    A function that sends an email to the addresses specified in the configuration file.
    Without authorization.
    Args:
        error (OSError): The error message to be sent
    """
    if config["smtp"]["enable"]:
        # add a text message to the email
        text = MIMEText(f'An error occurred while executing\n\n{error}')
        message.attach(text)

        logfile = config["logger"]["log_name"]
        files = [f'{logfile}.log', f'{logfile}_error.log']

        for i_name in files:
            part = attachment(i_name)
            if part is not None:
                message.attach(part)

        try:
            with smtplib.SMTP(config["smtp"]["smtp_server"], config["smtp"]["smtp_port"]) as server:
                server.sendmail(message['From'], config["smtp"]["to_email"], message.as_string())
        except smtplib.SMTPResponseException as smtp_err:
            error_code = smtp_err.smtp_code
            error_message = smtp_err.smtp_error
            logger.error(f"SMTP Error: {error_code} | {error_message}")
