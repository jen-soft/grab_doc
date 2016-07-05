# -*- coding: utf-8 -*-
from django.shortcuts   import render
from datetime           import datetime, timedelta
from calendar_line      import calendar_line
from spider.models      import get_one_record, Websites, Scans, FileLinks
from django.http        import HttpResponse, HttpResponseRedirect
import link
from spider.views       import system_state
import simplejson as json
from spider.views       import ScanApi
from django.core.cache  import cache


# главная страница сканирования - список сайтов
def index(request):
    count_days = 30  # количество дней для отрисовки сканирований (будет выбран периуд) [(сегодня-count_days):(сегодня)]
    start_data = datetime.now() - timedelta(days=count_days-1)  # отсчитываем от текущей даты
    # получаем упорядоченный список дат
    calendar_month = calendar_line(data_begin=start_data, count_days=count_days, group_by_month=True)
    #
    # извлекаем из базы сайты
    websites = Websites.objects.order_by('-id')
    websites.calendar_month = calendar_month  # список дат для отрисовки в темплейте
    for website in websites:
        # создаем календарный список по текущему сайту для размещения событий(сканировний)
        website.calendar = []
        # получаем список ЗАВЕРШЕННЫХ сканирований за последние [count_days] дней
        scans = Scans.objects.filter(website_id=website.id, data_finish__gt=start_data, is_deleted=False).order_by('-id')
        # перебераем все месяцы и дни из общего календаря, формируя календарь с данными для текущего сайта
        for month in websites.calendar_month:  # перебераем все дни за выбранный периуд
            for calendar_dey in month:
                # пакет данных закрепленный за конкретным днем :
                day_data = dict(data=calendar_dey, scans=[], count_file_links_new=0, last_scan=None)
                # перебираем все сканы для текущего сайта - ищим совпадение текущей даты и даты сканирования
                for scan in scans:
                    if calendar_dey != scan.data_finish.date():
                        continue
                    day_data['count_file_links_new'] += scan.count_file_links_new
                    day_data['scans'].append(scan)
                    day_data['last_scan'] = scan
                website.calendar.append(day_data)
        # статистика по сайту :
        website.count_total_scans      = Scans.objects.filter(website_id=website.id).count()      # всего сканов
        website.count_total_file_links = FileLinks.objects.filter(website_id=website.id).count()  # всего файловых ссылок

    return render(request, 'spider_admin/index.html', dict(websites=websites))
# ============================================================================


# ============================================================================
# обрабочик - добавление нового сайта в систему
def add_website(request):
    if request.method != 'POST':
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        try:
            url = request.POST.get('website', None)
            # добовляем ссылку на корень сайта :
            domain = link.get_full_domain(url)
            hash_domain = link.get_url_hash(domain)
        except:
            return HttpResponseRedirect('/')
        if len(Websites.objects.filter(hash_domain=hash_domain)) > 0 :
            return HttpResponse("website already is add.... <a href='/'>Go Home</a>")
        clean_link = link.get_url_protocol(url) + '://' + domain + '/'
        Websites(url=clean_link, hash_domain=hash_domain).save()
    return HttpResponseRedirect('/')  # перенаправляем на главную страницу сайта


def delete_website(request, website_id):
    website = get_one_record(Websites, id=website_id)
    if website is None:
        return HttpResponse("error: not valid website id <a href='/'>Go Home</a>")
    website.delete()
    return HttpResponseRedirect('/')  # перенаправляем на главную страницу сайта
# ============================================================================


# ============================================================================
# состояние системы - мониторинг работающих процессов
def get_system_status(request):
    return HttpResponse(json.dumps(dict(system_status=system_state())))
# ============================================================================


# ============================================================================
# доступ к всем найденным файлам по конкретному сайту
def get_all_file_links(request, website_id):
    return render(request, 'spider_admin/get_all_file_links.html', dict(website_id=website_id))


def get_file_links(request, website_id, count, start_id):
    website_id = int(website_id)
    count = int(count)
    start_id = int(start_id)
    #
    file_links = FileLinks.objects.filter(website_id=website_id, id__gt=start_id).order_by('id')[:count]
    for elm in file_links:
        print(elm.id,')',elm.url,'')
    print('start_id', start_id)
    result_html = render(request, 'spider_admin/get_file_links.html', dict(file_links=file_links, start_id=start_id)).getvalue()
    #
    last_elm_id = None
    if len(file_links) > 0:
        last_elm_id = file_links[len(file_links)-1].id
    #
    result = dict(result_html=result_html, last_elm_id=last_elm_id)
    return HttpResponse(json.dumps(result))
# ============================================================================


# ---------------   управление сканированием сайтов --------------------------
def start_scan(request, website_id):
    if get_one_record(Websites, id=website_id) is None:
        return HttpResponse(json.dumps(dict(result=False)))
    Scans(website_id=website_id).save()
    return HttpResponse(json.dumps(dict(result=True)))


def scan_stop(request, scan_id):
    scan = get_one_record(Scans, id=scan_id)
    if scan is None:
        return HttpResponse(json.dumps(dict(result=False)))
    # посылаем сигнал процессу что бы тот завершил свою работу (сохранив результат)
    ScanApi(scan.celery_task_id).stop_scan()
    return HttpResponse(json.dumps(dict(result=True)))


def scan_delete(request, scan_id):
    scan = get_one_record(Scans, id=scan_id)
    if scan is None:
        return HttpResponse(json.dumps(dict(result=False)))
    scan.is_deleted = True
    scan.save()
    return HttpResponse(json.dumps(dict(result=True)))
# ---------------  /управление сканированием сайтов --------------------------


# ============================================================================
# отображает сканирования на конкретный день + 10 последних ссылок по выбранному сканированию
def get_scan_by_data(request, website_id, year, month, day, number):
    scans = Scans.objects.filter(website_id=website_id,
                                 data_finish__year=year, data_finish__month=month, data_finish__day=day
                                 ).order_by('-id')
    number = int(number)
    if number < 0:
        number = 0
    if number >= len(scans)-1:
        number = len(scans)-1
    current_scan = scans[number]
    current_scan.file_links = FileLinks.objects.filter(scan_id=current_scan.id).order_by('-id')[:10]
    values = dict(scans=scans, current_scan=current_scan, website_id=website_id)
    return render(request, 'spider_admin/get_scan_by_data.html', values)

# TODO: создать функцию возвращающею ссылки по активному сканированию worker_api.get_status()['last_links']
# ============================================================================


# ============================================================================
# возвращает информацию по всем сайтам
# количество сканирований / файлов на весь сайт / состояние последнего сканирования
def get_websites_info(request):
    result = []
    # перебираем все сайты
    for website in Websites.objects.all():
        websites_info = cache.get("websites_info:%s:" % website.id)
        if websites_info is None:
            websites_info = dict(website_id=website.id)
            websites_info['count_scans']    = Scans.objects.filter(website_id=website.id).count()
            websites_info['count_files']    = FileLinks.objects.filter(website_id=website.id).count()
            websites_info['last_scan_info'] = get_website_last_scan_info(website.id)
            cache.set("websites_info:%s:" % website.id, websites_info, 5)
        result.append(websites_info)
    return HttpResponse(json.dumps(result))

STATUS_WAITING      = 'waiting'
STATUS_WORKING      = 'working'
STATUS_READY        = 'ready'
STATUS_TERMINATE    = 'terminate'


# возвращает информацию о сканировании по конкретному сайту
def get_website_last_scan_info(website_id):
    result = dict(scan_id=None, status=STATUS_READY)
    # получаем последнее сканирование для сайта :
    scan = get_one_record(Scans, order_by='-id', website_id=website_id, is_deleted=False)
    # нет сканов для текущего сайта
    if scan is None:
        return None

    result['scan_id'] = scan.id
    # сканирование завершено
    if scan.data_finish is not None: result['status'] = STATUS_READY
    # ожидает зауска
    elif scan.celery_task_id == '': result['status'] = STATUS_WAITING
    else :
        # получаем информацию о процессе сканировании
        worker_api = ScanApi(scan.celery_task_id)
        process_info = dict()
        process_info.update(worker_api.get_info())
        process_info['status'] = worker_api.get_status()
        result['process'] = process_info
        # сканирование ожижает остановки
        if ScanApi(scan.celery_task_id).is_need_terminate():  result['status'] = STATUS_TERMINATE
        else:                                                 result['status'] = STATUS_WORKING
    return result
# ============================================================================
