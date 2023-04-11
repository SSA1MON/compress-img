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
### Windows:
In the config.json file it is necessary to write the path to the directory with images in img_path
```
"img_path": "C:/Users/UserName/Documents/images"
```

Install additional libraries and can to run
```
pip install -r requirements.txt
```

## Configuration
```
"img_path" — Path to the directory with images
"image_format" — List of file extensions suitable for compression
"ignore_directories" — List of directories that are ignored
"max_warnings" — The number of warnings in a row, after which the script completes its work
"postfix" — Postfix in the file name after compression
"quality" — Percentage of preservation of the original image quality
            (100 is the original quality)
"log_name" — Name of the logging file
"rotation" — The period after which the main logging file will be archived
"connection_timeout" — Waiting time to connect to the storage (in seconds). Used to check the 
                       visit of each iterated path
"execution_timeout" — The working time of the compression function with the iterated file (in seconds). 
                      After the time has elapsed, it proceeds to work with the following file
"creation_days" — How long ago should the photo be created (in days)
```

## Releases
* [All releases](https://github.com/SSA1MON/compress-img/releases)

## Known issues
### Problems with Cyrillic in the Windows path

If Cyrillic is present in the path, you need to open the registry editor to solve the problem
```
1. Win + R
2. regedit
```
In the registry editor, you need to open the branch
```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage
```
Change the values of parameters 1250 (from c_1250.nls to c_1251.nls),
1251 (make sure that c_1251.nls), 1252 (from c_1252.nls to c_1251.nls)

Open Regional Standards Settings
```
Win + R
intl.cpl
```
Go to the "Advanced" tab. In the "Language of programs that do not support Unicode" make sure, 
that the current program language is "Russian (Russia)".

Then go to "Change the system language" and  uncheck "Beta version: 
Use Unicode UTF-8 to support the language worldwide".
Restart the PC.