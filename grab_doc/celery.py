# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals  # включаем абсолютные пути к файлам

import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grab_doc.settings')


# ----------------------------------------------------------- #
#          настраиваем главное celery приложение              #
app = Celery('grab_doc')
app.config_from_object('django.conf:settings')
# load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(    CELERY_TASK_SERIALIZER='json',
                    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
                    CELERY_RESULT_SERIALIZER='json',
                    CELERY_TIMEZONE='Europe/Oslo',
                    CELERY_ENABLE_UTC=True,             )


# ----------------------------------------------------------- #
#                добовляем свой функционал                    #
# возвращает количество воркеров для конкретной очереди или для всех очередей сразу
def get_count_workers(queue_name=None):
    count_workers = 0
    active_queues = app.control.inspect().active_queues()
    if active_queues is None:
        return 0
    for worker, queues in active_queues.items():    # 1 перебераем слОварь рабочих процессов
        for queue in queues:                    # 2 перебераем спИсок очередей которые они обслуживают
            if queue['name'] != queue_name:     # 3 из полученого словоря нам доступны ['name'] = u'scan_routing'
                continue
            count_workers += 1
    return count_workers


# отменить задание
def task_revoke(celery_task_id):
    app.control.revoke(celery_task_id, terminate=True, signal='SIGKILL')
# http://docs.celeryproject.org/en/latest/userguide/workers.html#revoke-revoking-tasks


# ----------------------------------------------------------- #

