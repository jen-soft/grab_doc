# -*- coding: utf-8 -*-
from django.contrib import admin

# Register your models here.
from models import Websites, Scans, FileLinks


class WebsitesAdmin(admin.ModelAdmin):
    list_display = ('id', 'hash_domain', 'url')
    pass
admin.site.register(Websites, WebsitesAdmin)


class ScansAdmin(admin.ModelAdmin):
    list_display = ('id', 'website_id', 'data_finish', 'celery_task_id', )
    pass
admin.site.register(Scans, ScansAdmin)


class FileLinksAdmin(admin.ModelAdmin):
    list_display = ('id', 'website_id', 'scan_id', 'parent', 'hash', 'url', 'data_update')
    pass
admin.site.register(FileLinks, FileLinksAdmin)