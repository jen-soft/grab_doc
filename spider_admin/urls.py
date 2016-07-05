# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # добавить / удалить сайт
    url(r'^add_new_website/', views.add_website, name='add_new_website'),
    url(r'^website/(?P<website_id>\d+)/delete/$', views.delete_website, name='delete_website'),

    # информация о состоянии работоспособности системы
    url(r'^system_status/$', views.get_system_status, name='bot.get_system_status'),

    # управление сканированием сайта
    url(r'^website/(?P<website_id>\d+)/start_scan/$', views.start_scan, name='start_scan'),
    url(r'^scan/(?P<scan_id>\d+)/stop/$', views.scan_stop, name='stop_scan'),
    url(r'^scan/(?P<scan_id>\d+)/delete/$', views.scan_delete, name='scan_delete'),

    # доступ к всем найденным файлам по конкретному сайту
    url(r'^website/(?P<website_id>\d+)/files/$', views.get_all_file_links, name='bot.get_all_file_links'),
    url(r'^website/(?P<website_id>\d+)/files/count/(?P<count>\d+)/start_id/(?P<start_id>\d+)/$',
        views.get_file_links, name='bot.get_file_links'),

    # отображает сканирования на конкретный день + 10 последних ссылок по выбранному сканированию
    url(r'^get_scan/website/(?P<website_id>\w+)'   r'/data/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})'
        r'/number/(?P<number>\w+)/$', views.get_scan_by_data, name='get_scan_by_data'),
    # get_scan/website/1/data/2016/02/18/number/3/

    # состояние последего сканирования по каждому сайту
    url(r'^get_websites_info/$', views.get_websites_info, name='get_websites_info'),


]
