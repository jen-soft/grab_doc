# -*- coding: utf-8 -*-
import link
from link import LinkBase
from grab.spider import Spider, Task
import sys, traceback
from threading import Thread

reload(sys)
sys.setdefaultencoding('utf-8')

def log(*args):
    result = ''
    for elm in args:
        result += str(elm)
    print(result)


class SpiderError(Exception):
    def __int__(self, message):
        self.__message = str(message)

    def __str__(self):
        return self.__message


# хранение ссылок на файлы
class FileLinks(object):
    def __init__(self):
        self.__file_links = []
        self.__keys = {}  # используем python словари для поиска дубликатов

    def add(self, file_url, parent_url, file_type):
        url_hash = link.get_url_hash(file_url)
        if self.__keys.get(url_hash, False):
            return
        self.__file_links.append(dict(hash=url_hash, file=file_url, type=file_type, parent=parent_url))

    def get(self):
        return self.__file_links

    def __len__(self): return len(self.__file_links)


# хранение ссылок которые не удалось открыть
class BadLinks(object):
    def __init__(self):
        self.__file_links = []

    def add(self, url, parent_url):
        self.__file_links.append([url, parent_url])

    def get(self):
        return self.__file_links

    def __len__(self): return len(self.__file_links)


class SimpleSpider(Spider):
    # TODO: необходимо задать максимальный размер загружаемой страницы
    def __init__(self, **kwargs):
        super(SimpleSpider, self).__init__(**kwargs)
        self.__links = LinkBase()           # класс хранения и учета посещения веб ссылок
        self.__file_links = FileLinks()     # класс хранения ссылок (file_url, parent_url, file_type)
        self.__bad_links  = BadLinks()      # класс хранения ссылок которые не удалось открыть
        self.file_types = []                # типы файлов
        #
        self.__count_grab_pages = 0         # количество посещенных страниц
        self.__stopped_by_user = False      # если процесс сканирования прервал пользователь
        #
        self.__task_id = 0                  # порядковый номер задачи
        self.thread             = Thread(target=self.run)
        self._process_is_ready  = False
    # -------------------------------------------------------

    def run(self):
        super(SimpleSpider, self).run()
        self._process_is_ready = True

    def start(self, start_url, deep_level, file_types):
        if type(file_types) is str:
            self.file_types = [file_types, ]
        if type(file_types) is not list and type(file_types) is not list:
            raise SpiderError('not correct file type - use list or type format')
        self.file_types = file_types
        # добовляем ссылку на корень сайта :
        root_link = link.get_url_protocol(start_url) + '://' + link.get_full_domain(start_url)
        self.__links.add(url=root_link, level=deep_level)
        # запускаем процесс сканирования в отдельном потоке
        self._process_is_ready = False
        self.thread.start()

    # завершился ли процесс сканирования :
    def process_is_ready(self): return self._process_is_ready

    # -------------------------------------------------------

    # -------------------------------------------------------
    # Результат выполнения
    def get_file_links(self): return self.__file_links.get()  # [{hash:x, file:x, type:x, parent:x}, ]
    def get_bad_links(self):  return self.__bad_links.get()   # [[], [url, parent_url], ... ]
    # -------------------------------------------------------

    # -------------------------------------------------------

    # -------------------------------------------------------
    # информация о процессе выполения, доступная для асинхронного чтения
    def get_count_vised_pages(  self): return self.__count_grab_pages
    def get_count_indexed_links(self): return self.__links.get_count_indexed_links()
    def get_count_new_links(    self): return self.__links.get_count_new_links()
    def get_count_file_links(   self): return len(self.__file_links)
    def get_current_link_level( self): return self.__links.get_current_link_level()
    # -------------------------------------------------------

    # -------------------------------------------------------
    #                =  E N G I N E  =
    # вызывается при запуске процесса сканирования
    def task_generator(self):
        new_link = self.__links.get_not_vised()
        if new_link is None:
            print('ERROR - no any free links for start scan.')
            return
        url, level = new_link
        yield Task('begin', url=url, url_deep=level)

    # decorator - подсчитывает количество запущенных заданий и генерирует новые
    def task_counter(fn):
        def wrapper(self, *args, **kwargs):
            try:
                fn(self, *args, **kwargs)
            except:
                print('=======================')
                self.stop()
                log('<****ERROR****>', sys.exc_info())
                tb = sys.exc_info()[2]
                log(traceback.format_tb(tb)[0])
                # https://desktop.arcgis.com/ru/arcmap/10.3/analyze/python/error-handling-with-python.htm
                print('=======================')
                raise
            #
            self.__count_grab_pages += 1
            # необходимо досканировать ссылки "начального" уровня до перехода на следующий
            if self.__links.is_new_link_level():  #
                if self.task_queue.size() > 0:
                    return
                print('---------new link level------------', self.__links.get_current_link_level())
            #
            while self.task_queue.size() < (self.thread_number * 10):
                new_link = self.__links.get_not_vised()
                # TODO: можно внедрить систему хранения родительской ссылки - что бы при ошибки оследить цепочку переходов
                if new_link is None:
                    return
                url, level = new_link
                self.add_task(Task('begin', url=url, url_deep=level))
            if self.task_queue.size() < 1:
                print('************************ all task ready !!! *************************** ')
                pass  # task ready !
        return wrapper

    def task_begin_fallback(self, task):
        print(' ERROR: TASK NOT MAKED!!!!', task.url)
        # TODO: сделать список ссылок не открытых
        # TODO: пройтись по неоткрытым ссылкам перед переходом на новый уровень

    # переопределили метод добовления заданий для учета количества запущенных заданий
    def add_task(self, task, raise_error=False):
        super(SimpleSpider, self).add_task(task, raise_error)

    # обрабатывает страницы которые загрузились:
    #  <****ERROR****>(<type 'exceptions.TypeError'>,
    # TypeError("'NoneType' object has no attribute '__getitem__'",),
    # <traceback object at 0xb59200a4>)
    @task_counter
    def task_begin(self, grab, task):
        self.__task_id += 1
        task_url_deep = task.url_deep
        # fine all links on this loaded page.
        for elem in grab.xpath_list('//a'):
            url_src = elem.get('href')
            #
            if url_src is None:
                continue  # temp url
            url_src = grab.make_url_absolute(url_src)
            new_url = url_src.lower()  # символамы приведённым к нижнему регистру
            #
            if new_url.startswith(('mailto:', 'javascript:', 'tel:')):
                continue
            #
            if not new_url.startswith(('http://', 'https://', 'ftp://', 'file://', 'feed://')):
                # log('error link is not correct (***(!)***) ', new_url, 'parent= ', grab.response.url)
                self.__bad_links.add(url=new_url, parent_url=grab.response.url)
                continue
            #
            new_url = link.cut_url(new_url, '#')  # cut anchor-s   from new    url
            if new_url == '' or new_url == '/':
                continue  # no visit temp urls
            #
            # не корректный вариант ссылки :
            if link.get_full_domain(url=new_url) is None:
                # log('error link is not correct (***(!)***) ', new_url)
                self.__bad_links.add(url=new_url, parent_url=grab.response.url)
                continue
            #
            if self.__links.is_indexed(url=new_url):
                # log('link already is_indexed')
                continue  # new url already index-ed :
            #
            # проверяем ведет ли ссылка на файл
            if link.is_file(new_url):
                self.__links.add(url=new_url, level=0, is_visit=True)
                if link.is_file(new_url, self.file_types):
                    # log('is_our_file->', new_url)
                    self.__file_links.add(file_url=url_src, parent_url=task.url, file_type=new_url[-4:])
                    continue
                # log('is_file->', new_url)
                continue
            #
            # grab only url from domain:
            if not link.is_url_in_domain(url=new_url, parent_url=task.url, level_domain=2):
                # log('url not from our domain (***(!)***)')
                continue  # url not from our domain
            #
            # save NEW url in store
            if task_url_deep > 0:
                new_url_deep = task_url_deep - 1
                # log('url add/ new_url_deep',new_url_deep ,' |new_url= ',new_url)
                self.__links.add(url=url_src, level=new_url_deep)

# ================================================================
