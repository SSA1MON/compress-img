# Скрипт для сжатия изображений

<p align="center">
<img src="https://img.shields.io/github/repo-size/SSA1MON/compress-img?label=size" alt="repo-size">
<img src="https://img.shields.io/github/v/release/SSA1MON/compress-img" alt="open-issues">
<img src="https://img.shields.io/github/languages/top/SSA1MON/compress-img" alt="language">
<img src="https://img.shields.io/github/last-commit/SSA1MON/compress-img" alt="commits">
</p>

## Описание
Скрипт работает на базе [mozjpeg](https://github.com/mozilla/mozjpeg) by Mozilla. 
Получает на вход путь, проходится по всем директориям внутри, сжимает изображения
создавая копию файла с постфиксом и удаляет оригинал.

Посмотреть команды: 
```
cjpeg -h
```

## Как запустить
В файле config.py прописываем путь к директории с изображениями в img_path
```
img_path = Path("C:/Users/ИмяПользователя/Documents/images")
```

Устанавливаем дополнительные библиотеки и можно запускать
```
pip install pathlib
pip install loguru
```

## Releases
* [All releases](https://github.com/SSA1MON/compress-img/releases)

## Известные проблемы
### Проблемы с кириллицей в пути

Если в пути присутствует кириллица:

Для решения проблемы нужно открыть редактор реестра
```
1. Win + R
2. regedit
```
В редакторе реестра необходимо открыть ветку
```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage
```
Изменить значения параметров 1250 (с c_1250.nls на c_1251.nls), 
1251 (убедится что c_1251.nls), 1252 (с c_1252.nls на c_1251.nls).

Открыть настройки региональных стандартов
```
Win + R
intl.cpl
```
Перейти во вкладку «Дополнительно». В «Язык программ, не поддерживающих Юникод» убедиться, 
что выбран текущий язык программ «Русский (Россия)». 

Далее перейти «Изменить язык системы» и
убрать галочку с «Бета версия: Использовать Юникод UTF-8 для поддержки языка во всем мире».
Перезагрузить ПК.