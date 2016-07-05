# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError


def get_one_record(model, order_by=None, **kwargs):
    if order_by is not None:
        records = model.objects.filter(**kwargs).order_by(order_by)[:1]
    else:
        records = model.objects.filter(**kwargs)[:1]
    if len(records) < 1:
        return None
    return records[0]


class Websites(models.Model):
    url = models.CharField(max_length=255, unique=True)
    hash_domain = models.CharField(max_length=32, unique=True)


class Scans(models.Model):
    website = models.ForeignKey(Websites, on_delete=models.CASCADE)     # id сайта
    data_finish = models.DateTimeField(blank=True, null=True, default=None)           # дата завершения сканирования

    # class Meta: # по какой то причине у меня не работает в SqlLight
    #     unique_together = ('website', 'data_finish',)  # связка уникальных полей
    # пишу свою проверку
    @transaction.atomic  # django транзакции - буфферизированный диступ к базе данных
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        in_base = get_one_record(Scans, website_id=self.website.id, data_finish=self.data_finish)
        if in_base is not None:
            if in_base.id != self.id :
                # msg = self.unique_error_message(self.__class__, (self.website, self.data_finish))
                raise ValidationError('scan already exist', code='invalid')
        return super(Scans, self).save(force_insert, force_update, using, update_fields)

    deep_level = models.IntegerField(default=9)                         # максимальный уровень прохождения по ссылкам

    celery_task_id = models.CharField(max_length=36, default='')    # id celery процесса

    count_vised_pages = models.IntegerField(default=0)              # количество открытых страниц
    count_file_links_total = models.IntegerField(default=0)         # количество найденных файловых ссылок
    count_file_links_new = models.IntegerField(default=0)           # сколько найдено новых файловых ссылок

    is_deleted = models.BooleanField(default=False)


class FileLinks(models.Model):
    website = models.ForeignKey(Websites, on_delete=models.CASCADE,  null=True, default=0)
    scan = models.ForeignKey(Scans, on_delete=models.CASCADE)
    parent = models.CharField(max_length=255, default='')
    url = models.CharField(max_length=255)
    hash = models.CharField(max_length=32)
    type = models.CharField(max_length=16, default='')
    data_update = models.DateTimeField(auto_now=True, blank=True, null=True)