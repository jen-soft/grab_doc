# -*- coding: utf-8 -*-
author: Евгений jen
email: jen.soft.master@gmail.com

description: Система поиска файлов на сайтах

django приложения :
    spider          - система сканирования сайтов
    spider_admin    - пользовательский интерфейс для управления сканированием

Используемые компоненты:
django      управление моделями, веб интерфейс
Grab.Spider веб паук
celery      запуск задачь как отдельные процессы
redis       брокер сообщений для celery,
            система хранения кэша для django,
            самописная очередь сообщений - для управления состоянием процесса сканирования
Sqlite/PostgreSql - сервис хранения данных
supervisor  - управление процессами
virtualenv  - рабочее окружение (програмная оболочка проекта)
git         - система контроля версий


при желании использовать PostgreSql
    sudo apt-get install postgresql postgresql-contrib
    важно для локальной машины!
    sudo nano /etc/postgresql/9.5/main/pg_hba.conf
    изменить   local   all             postgres                                peer
    на         local   all             postgres                                md5
    * логинится от суперпользователя иначе будет пустой файл!
    перезагружаем конифг:
    sudo service postgresql restart

    создаем пользователя базы
    sudo -u postgres psql
        CREATE DATABASE test_database;
        CREATE USER test_user WITH password 'qwerty';
        GRANT ALL privileges ON DATABASE test_database TO test_user;
    список пользователей    \du
    список баз данных       \l
    описание команд         \?
    удалить базу            DROP DATABASE my_db_name;
    удалить пользователя    DROP ROLE my_username;

    настройка проекта на работу с postgresql
    pip install psycopg2

    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'my_base',
        'USER': 'my_base_user',
        'PASSWORD': 'my_user_password',
        'HOST': '',  # Set to empty string for localhost.
        'PORT': '',  # Set to empty string for default.
    }

    * графическая оболочка для postgresql > pgAdmin
        sudo apt-get install pgadmin3
    15 команд postgresql            http://sys.dmitrow.com/node/205
    доходчевое описание работы      https://www.mvoronin.pro/en/blog/post-8
                                    http://eax.me/postgresql-install/
                                    https://habrahabr.ru/post/137121/
