COMPRESS = {
    "img_path": "PATH_IS_HERE",
    "image_formats": [".jpg", ".jpeg", ".png"],
    "ignore_directories": ["dir_name"],
    "postfix": "_compressed",
    "quality": 20,
    "creation_days": 0
}
SMTP = {
    "enable": False,
    "from_email": "sender@domain.com",
    "to_email": ["first@domain.com", "second@domain.com"],
    "smtp_address": "smtp.domain.com",
    "smtp_port": 465
}
LOGGER = {
    "log_name": "compress",
    "rotation": "1 week, 6 days"
}
TIMEOUT = {
  "connection_timeout": 5,
  "execution_timeout": 30
}
