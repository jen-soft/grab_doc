# -*- coding: utf-8 -*-
from celery.task        import task, periodic_task
from datetime           import datetime, timedelta
from django.core.cache  import cache
from grabdoc.celery     import task_revoke, get_count_workers
from models             import get_one_record, Scans, FileLinks, Websites
from RedisBuffer        import RedisBuffer
import time
from threading          import Thread
from SimpleSpider       import SimpleSpider
from sqlite3            import OperationalError
from django.db          import transaction


# состояние системы
def system_state():
    system_status = cache.get('system_status')
    if system_status is None:
        system_status = True
        if   get_count_workers(queue_name='scan_routing') < 1: system_status = False
        elif get_count_workers(queue_name='scan_worker')  < 1: system_status = False
        cache.set('system_status', system_status, 5)
    return system_status
# http://djbook.ru/rel1.5/topics/cache.html


# межпроцессорное взаимодействие с процессом сканирования
class ScanApi(RedisBuffer):
    def __init__(self, worker_id):
        super(ScanApi, self).__init__(name=worker_id)

    def update_watchdog_time(self): self.set(watchdog_time=time.time())
    def get_response_time(self):    return time.time() - self.get('watchdog_time', 0)

    STATUS_UNDEFINED = None
    STATUS_WORKING  = 'working'
    STATUS_SAVING   = 'saving'
    STATUS_READY    = 'ready'

    def set_status(self, status): self.set(status=status)
    def get_status(self): return self.get('status', default=self.STATUS_UNDEFINED)

    def stop_scan(self): self.set(stop_scan=True)
    def is_need_terminate(self): return self.get('stop_scan', default=False)

    def set_info(self, **kwargs):
        lst_info = self.get_info()
        lst_info.update(kwargs)
        self.set(process_info=lst_info)
    # * set_info - функция не потоко безопасна - использовать только в одном потоке/процессе .
    def get_info(self): return self.get('process_info', default=dict())


# запуск сканирований сайта
@periodic_task(run_every=timedelta(seconds=30))
def scan_routing():
    # проверяем работоспособность системы :
    if system_state() is False:
        print('warning: system not ready - no any workers for scan')
        return
    #
    # удаление сканирований
    scans_terminate = Scans.objects.filter(data_finish=None, is_deleted=True).order_by('website_id')
    for scan in scans_terminate:
        task_revoke(scan.celery_task_id)  # пытаемся удплить celery задание
        scan.delete()

    count_working_scans = 0
    # получаем все записи где помечено что процесс работает
    scans_working = Scans.objects.filter(data_finish=None).exclude(celery_task_id='').order_by('website_id')
    for scan in scans_working:
        # почему то celery_app.control.inspect().active()
        # не всегда возвращает полную информацию по активным процессам,
        # поэтому я использую самописную систему проверки - работает ли исполняющий поток
        if ScanApi(worker_id=scan.celery_task_id).get_response_time() < 90:  # секунд
            count_working_scans += 1
            continue
        print('ERROR: task is not working: ', scan.celery_task_id)
        # TODO: проверить через AsyncResult упала ли задача из за exception - ну и что то с этим сделать O_o
        task_revoke(scan.celery_task_id)                    # пытаемся удплить celery задание
        FileLinks.objects.filter(scan_id=scan.id).delete()  # удаляем все добавленные ссылки
        scan.celery_task_id = ''
        scan.save()
    # *!* в настройках [CELERYD_PREFETCH_MULTIPLIER = 1] что бы процесс не резервировал за собой более чем 1 задачу

    # проверяем доступны ли нам исполнители
    count_free_workers = get_count_workers(queue_name='scan_worker') - count_working_scans
    if count_free_workers <= 0:
        return

    # 4 запускаем сканирования сохраняя на их указатель
    scans_waiting = Scans.objects.filter(data_finish=None, celery_task_id='').order_by('website_id')
    for scan in scans_waiting:
        if count_free_workers < 1:
            break
        count_free_workers -= 1
        scan.celery_task_id = scan_worker.delay(scan_id=scan.id)
        scan.save()


@task
def scan_worker(scan_id):
    celery_task_id = scan_worker.request.id
    print('###[start scan]>',celery_task_id)
    thread = Thread(target=scanner, kwargs=dict(scan_id=scan_id, celery_task_id=scan_worker.request.id))
    thread.start()
    scan_api = ScanApi(celery_task_id)
    while thread.isAlive():
        scan_api.update_watchdog_time()  # сообщаем что процесс не умер
        time.sleep(1)
    print('###[scan finished]>',celery_task_id, '<###[end]')


def scanner(scan_id, celery_task_id):
    scan_api = ScanApi(celery_task_id)
    scan_api.set_status(scan_api.STATUS_WORKING)
    scan = get_one_record(Scans, id=scan_id)
    website = get_one_record(Websites, id=scan.website_id)
    #

    # создаем экземпляр сканера
    spider = SimpleSpider(thread_number=1)
    spider.start(start_url=website.url, deep_level=scan.deep_level, file_types=['pdf',])
    total_time = 0
    while not spider.process_is_ready():
        if scan_api.is_need_terminate():
            spider.stop()
            break
        total_time += 1
        time.sleep(1)

        # каждые 5 секунд обновляем информацию о сканировании
        if total_time % 5 == 0:
            scan_api.set_info(count_file_links=spider.get_count_file_links(),
                              count_opened_pages=spider.get_count_vised_pages()
                              #last_links=spider.get_file_links(10)
                              )

    # далее сохранение
    scan_api.set_status(scan_api.STATUS_SAVING)
    scan = get_one_record(Scans, id=scan_id)
    website = get_one_record(Websites, id=scan.website_id)

    # получаем найденыне ссылки ссылки
    file_links = spider.get_file_links()  # [{hash:x, file:x, type:x, parent:x}, ]
    # сохраняем результат небольшими транзациями - что бы снять нагрузку с базы данных
    COUNT_RECORDS_FOR_STEP = 10000      # количес записей в одном сохранении
    TIME_WAITING = 60                   # время ожидания между сохранениями
    count_file_links_new = 0            # количество новых ссылок
    cursor = 0
    while cursor < len(file_links):
        count_new = safely_save(website.id, scan_id, file_links[cursor:(cursor+COUNT_RECORDS_FOR_STEP)])
        cursor += COUNT_RECORDS_FOR_STEP
        time.sleep(TIME_WAITING)
        count_file_links_new += count_new
        if cursor > len(file_links): cursor = len(file_links)
        scan_api.set_info(count_saved_links=cursor)

    # сохраняем отчет об сканировании :
    scan.refresh_from_db()
    scan.count_file_links_new = count_file_links_new  # новых ссылок
    scan.count_vised_pages = spider.get_count_vised_pages()  # число посещенных страниц
    scan.celery_task_id = ''
    scan.data_finish = datetime.now()
    scan.save()
    #
    # # ссылки которые не удалось обработать :
    # bad_links = self.web_bot.get_bad_links()  # [[], [url, parent_url], ...]
    # for url, parent_url in bad_links:
    #     log('BAD LINK, url: ', url, '   |parent: ', parent_url)
    #
    scan_api.set_status(scan_api.STATUS_READY)


# сохранение данных в многопроцессорной среде для SqlLight
def safely_save(website_id, scan_id, links):
    while True:
        try:
            return save_file_links(website_id, scan_id, links)
        except OperationalError:
            print('error: date base is locked.')
            time.sleep(1)


@transaction.atomic  # django транзакции - буфферизированный диступ к базе данных
def save_file_links(website_id, scan_id, links):
    print('saving...')
    count_file_links_new = 0

    for elm in links:
        old_link = get_one_record(FileLinks, hash=elm['hash'], website_id=website_id)
        if old_link is not None:
            old_link.save()  # update data scan
        else:
            FileLinks(website_id=website_id, scan_id=scan_id, parent=elm['parent'],
                      url=elm['file'], hash=elm['hash'], type=elm['type']).save()
            count_file_links_new += 1
    return count_file_links_new


