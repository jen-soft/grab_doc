#!/bin/bash
# ---------------------------------------------------------------------------------------------------------------------#
# скрипт для запуска всех необходимых программ проекта в фоновом режиме.
# (как запустить скрипт - описано внизу файла)
# ---------------------------------------------------------------------------------------------------------------------#
echo
echo '('$(date +%Y-%m-%d/%H:%M.%S)')---------< start the grab_doc project >--------------'

source ~/work/env/grab_doc/bin/activate       # активируем виртуальное оуружение
cd ~/work/grab_doc                            # переходим в папку с проектом

#                      - запускаем необходимые процессы -                                                              #

# django - веб фреймворк
nohup python manage.py runserver 8001 >logs/django.log &

# flower - состояние выполнения celery задач ( http://127.0.0.1:5555/ )
nohup python manage.py celery flower --address=127.0.0.1 --port=5555  --log_to_stderr --logging=INFO >logs/celery.flower.log &

# celery cam - состояние переодических заданий в adnim панели django ( http://127.0.0.1:8000/admin/djcelery )
nohup python manage.py celerycam --frequency=10.0 --loglevel=INFO >logs/celery.cam.log &

# celery beat - генерирует задания (scheduler) исходя из списка переодических заданий сохранненых в (django-orm)
nohup python manage.py celerybeat >logs/celery.beat.log &



# worker - запуск рабочего процесса для выполнения заданий: (можно запустить несколько)
nohup python manage.py celery worker --concurrency=1 --loglevel=INFO --app=grab_doc --queues=scan_routing --hostname=worker.scan_routing  --purge >logs/worker.scan_routing.log &
nohup python manage.py celery worker --concurrency=1 --loglevel=INFO --app=grab_doc --queues=scan_worker  --hostname=worker.scan_worker.1 --purge >logs/worker.scan_worker.1.log &
nohup python manage.py celery worker --concurrency=1 --loglevel=INFO --app=grab_doc --queues=scan_worker  --hostname=worker.scan_worker.2 --purge >logs/worker.scan_worker.2.log &
nohup python manage.py celery worker --concurrency=1 --loglevel=INFO --app=grab_doc --queues=scan_worker  --hostname=worker.scan_worker.3 --purge >logs/worker.scan_worker.3.log &



# ----------------------------------------------------------------------------------------------------------------------
# ЗАПУСК ./bash.run.grab_doc.sh
# для того, чтоб скрипт можно было запустить, надо изменить права доступа к нему,
# добавив возможность исполнения файла: chmod a+x bash.run.grab_doc.sh
# http://www.bash-scripting.ru/abs/chunks/ch04.html
# http://linuxgeeks.ru/bash-intro.htm
#
# список запущенных python программ:
# ps aux | grep python
# ps aux | grep manage.py 
# убить процессы  pkill -f manage.py
# http://vds-admin.ru/unix-toolbox/processes
# https://www.opennet.ru/docs/RUS/lnx_process/process2.html
# http://heap.altlinux.org/tmp/unix_base/ch04s05.html
# ----------------------------------------------------------------------------------------------------------------------
