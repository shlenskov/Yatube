# Yatube - социальная сеть. 

## Она дает пользователям следующие возможности:
- создание учетной записи;
- публикации записей в сообществе;
- возможность публикации в записи изображений;
- подписка на любимых авторов;
- комментарии к записям других авторов;
- отмечать понравившиеся записи;
- просмотр ленты с записями, на которые оформлена подписка.


## Как запустить проект:

- Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:shlenskov/Yatube.git  
  
cd api_final_yatube
```
  
- Cоздать и активировать виртуальное окружение:

> для MacOS:

```
python3 -m venv env

source venv/bin/activate 
```
  
> для Windows:

```
python -m venv venv

source venv/bin/activate

source venv/Scripts/activate
```
  
- Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
  
python3 -m pip install --upgrade pip
```

- Выполнить миграции:

```
python3 manage.py migrate
```
  
- Запустить проект:

```
python3 manage.py runserver  
```


Автор: Шленсков Владимир.
