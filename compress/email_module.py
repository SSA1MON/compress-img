import smtplib
from loguru import logger

from main import config


def send_email(error: OSError) -> None:
    """
    A function that sends an email to the addresses specified in the configuration file.
    Without authorization.
    Args:
        error (str): The error message to be sent
    """
    if config["smtp"]["enable"]:
        subject = "Compression execution error"
        from_addr = config["smtp"]["from_email"]
        to_addr = config["smtp"]["to_email"]
        body_content = f"An error occurred while executing\n\n{error}"

        email_content = "\r\n".join((
            f"From: {from_addr}",
            f"To: {to_addr}",
            f"Subject: {subject}",
            "",
            body_content
        ))
        try:
            with smtplib.SMTP(config["smtp"]["smtp_server"], config["smtp"]["smtp_port"]) as server:
                server.sendmail(from_addr, to_addr, email_content)
        except smtplib.SMTPResponseException as smtp_err:
            error_code = smtp_err.smtp_code
            error_message = smtp_err.smtp_error
            logger.error(f"SMTP Error: {error_code} | {error_message}")
