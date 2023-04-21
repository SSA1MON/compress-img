# Script for image compression

<p align="center">
<img src="https://img.shields.io/github/repo-size/SSA1MON/compress-img?label=size" alt="repo-size">
<img src="https://img.shields.io/github/v/release/SSA1MON/compress-img" alt="open-issues">
<img src="https://img.shields.io/github/languages/top/SSA1MON/compress-img" alt="language">
<img src="https://img.shields.io/github/last-commit/SSA1MON/compress-img" alt="commits">
</p>

## Description
The script is based on [pillow](https://github.com/python-pillow/Pillow) library. 
Receives the input path, goes through all the directories inside, compresses the images
creating a copy of the file with a postfix and deletes the original.

## How to launch
Create a virtual environment and activate it
```
python3 -m venv compress-env
source compress-env/bin/activate
```
Installing dependent libraries
```
pip3 install -r requirements.txt
```
In the config.json file it is necessary to write the path to the directory with images 
in img_path
```
"img_path": "/home/user"
```
Run
```
python3 compress/main.py
```

## Configuration
```
compress:
"img_path" — Path to the directory with images
"image_format" — List of file extensions suitable for compression
"ignore_directories" — List of directories that are ignored
"postfix" — Postfix in the file name after compression
"quality" — Percentage of preservation of the original image quality
(100 is the original quality)
"creation_days" — How long ago should the photo be created (in days)

smtp:
"enable" — Activating mail sending (true or false)
"from_email" — Sender email address
"to_email" — List of recipient addresses
"smtp_server" — SMTP Server Address
"smtp_port" — SMTP Server Port

logger:
"log_name" — Name of the logging file
"rotation" — The period after which the main logging file will be archived
"connection_timeout" — Waiting time to connect to the storage (in seconds).
Used to check the visit of each iterated path
"execution_timeout" — The working time of the compression function with the
iterated file (in seconds). After the time has elapsed, it proceeds to work 
with the following file
```

## Links
* [All releases](https://github.com/SSA1MON/compress-img/releases)
* [Issues](https://github.com/SSA1MON/compress-img/issues?q=is%3Aissue+is%3Aclosed)