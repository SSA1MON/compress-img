# Script for image compression

<p align="center">
<img src="https://img.shields.io/github/repo-size/SSA1MON/compress-img?label=size" alt="repo-size">
<img src="https://img.shields.io/github/v/release/SSA1MON/compress-img" alt="open-issues">
<img src="https://img.shields.io/github/languages/top/SSA1MON/compress-img" alt="language">
<img src="https://img.shields.io/github/last-commit/SSA1MON/compress-img" alt="commits">
</p>

## Description
The script is based on [mozjpeg](https://github.com/mozilla/mozjpeg ) by Mozilla. 
Receives the input path, goes through all the directories inside, compresses the images
creating a copy of the file with a postfix and deletes the original.

View commands: 
```
cjpeg -h
```

## How to launch
### Windows:
In the config.py file it is necessary to write the path to the directory with images in img_path
```
img_path = Path("C:/Users/ИмяПользователя/Documents/images")
```

Install additional libraries and can to run
```
pip install pathlib
pip install loguru
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