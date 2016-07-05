# -*- coding: utf-8 -*-
import re
import hashlib


def get_url_hash(url):                                 # https://www.ms.gov.md/some?vars=1#ancor
    url = cut_url(url, '#')                            # https://www.ms.gov.md/some?vars=1
    if url[-1:] == '/':
        url = url[:-1]                                 # https://www.ms.gov.md/some?vars=1
    domain = get_full_domain(url)                      #         www.ms.gov.md
    if domain is None:
        return None
    # url = url.lower()
    if domain[:4] == 'www.':
        domain = domain[4:]                            #             ms.gov.md
    url = url[url.index(domain):]                      #             ms.gov.md/some?vars=1#ancor
    return hashlib.md5(url).hexdigest()  # take hash of url address


def cut_url(url, key, start=0):
    try:
        return url[:url.index(key, start)]
    except ValueError:
        return url


def get_full_domain(url, level=None):                   # https://ms.gov.md/some?vars=1#ancor
    m = re.findall(r'[^:]+$', url)                      #       //ms.gov.md/some?vars=1#ancor
    if len(m) < 1:
        return None
    m = m[0]
    # IndexError: list index out of range
    url_parts = re.findall(r'[^/]+', m)
    if len(url_parts) < 1:
        return None
    full_domain = url_parts[0]                          #         ms.gov.md
    domain_parts = re.findall(r'[^.]+', full_domain)    #         ms.gov.md   (to=>)   ['ms', 'gov', 'md']
    domain_parts.reverse()                              #                              ['md', 'gov', 'ms']
    #
    if len(domain_parts) < 2:
        return None
    #
    if level is None:
        return full_domain
    #
    if len(domain_parts) < level:
        level = len(domain_parts)
    result = domain_parts[0]
    current_part_id = 1
    while current_part_id < level:
        result = domain_parts[current_part_id] + '.' + result
        current_part_id += 1
    return result


# функция не оптимизированна
# mailto:mamonoff01@gmail.com
# http://subscribe.ru/catalog/help.memory
# ftp://files.zipsites.ru/
# http://www.mid.ru/brp_4.nsf/newsline/2B4694CD44B6411E44257974003E49C4
# http://www.picknettprince.com/http://www.picknettprince.com/
def is_file(url, file_types=None):
    if type(file_types) is str:
        file_types = [file_types, ]
    #
    url = cut_url(url, '?')  # cut anchor-s     from url
    url = cut_url(url, '#')  # cut parameter-s  from url
    #
    if file_types is not None:
        for file_type in file_types:
            if url[-len(file_type):] == file_type:
                return True
        return False
    #
    # вырезаем доменное имя
    if url[:4] == 'http' or url[:4] == 'ftp':
        domain = get_full_domain(url)
        indent = url.index(domain) + len(domain) + len('/')
        if indent >= len(url):
            return False
        url = url[indent:]
    #
    # получаем только имя файла
    full_file_name = re.findall(r'[^/]+$', url)
    if len(full_file_name) < 1:
        return False
    full_file_name = full_file_name[0]
    if len(full_file_name) < 3:
        return False
    #
    if full_file_name[:7] == 'mailto:': # mailto:mamonoff01@gmail.com
        return False
    #
    # получаем тип файла :
    file_type = re.findall(r'[^.]+$', full_file_name)  # search letters, before haven't fined dot , start from end of string
    if len(file_type) < 1:
        return False
    file_type = file_type[0]
    if len(file_type) == len(full_file_name):
        return False
    if len(file_type) > 6:
        return False
    # web files :
    elif file_type == 'html'    :  return False
    elif file_type == 'htm'     :  return False
    elif file_type == 'php4'    :  return False
    elif file_type == 'php'     :  return False
    elif file_type == 'asp'     :  return False
    elif file_type == 'aspx'    :  return False
    elif file_type == 'torrent' :  return False
    else:                          return True
    #


def is_url_in_domain(url, parent_url, level_domain=2):
    url_domain = get_full_domain(parent_url, level_domain)  # er.my.ru
    url = cut_url(url, '?')  # cut parameters from parent url
    url = cut_url(url, '#')  # cut anchor-s   from new    url
    try:
        if url.index(url_domain) >= 0:
            return True
    except ValueError:
        pass
    return False


def get_url_protocol(url):
    m = re.findall(r'[a-zA-Z]+', url)
    if m[0] == 'https':
        return 'https'
    return 'http'


def make_url_global(full_url, current_url):
    # HAVE BUG [ 2016-06-02 16:46 ]
    parent_url = cut_url(full_url, '?')  # cut parameters from parent url
    url = current_url
    #
    if url[:5] == u'http:' or url[:6] == u'https:':
        return url  # if url already global :
    #
    # if link from root of site
    if url[:1] == '/':
        domain = get_full_domain(parent_url)  # https                         https://gov.md/sm?vr=1#ancor
        protocol = get_url_protocol(parent_url)  # gov.md                        https://gov.md/sm?vr=1#ancor
        return protocol + '://' + domain + url  # https + :// + gov.md + [url]
    # than link is relative :
    if parent_url[-1:] != '/':
        parent_url += '/'
    return parent_url + url


class LinkBase(object):
    def __init__(self):
        self.__links_new = []
        self.__links_hash = dict()
        self.__lastLinkLevel = -1

    def add(self, url, level, is_visit=False):
        url_hash = get_url_hash(url=url)
        #
        try:
            return self.__links_hash[url_hash]
        except KeyError:
            self.__links_hash[url_hash] = True
        #
        # add link as already vised
        if is_visit:
            return True
        #
        self.__links_new.append([url, level])  # add to edn of query
        return True

    def get_not_vised(self, set_as_vised=True):
        try:
            if set_as_vised:
                link = self.__links_new.pop(0)  # get from head of query
            else:
                link = self.__links_new[0]
            self.__lastLinkLevel = link[1]
            return link
        except IndexError:
            return None

    def is_indexed(self, url):
        url_hash = get_url_hash(url=url)
        try:
            if self.__links_hash[url_hash] is not None:
                return True
        except KeyError:
            return False

    # if changed deep url level
    def is_new_link_level(self):
        if len(self.__links_new) < 1:
            return True
        (url, level) = self.__links_new[0]
        if level != self.__lastLinkLevel:
            return True
        return False

    def get_current_link_level(self):
        try:
            return self.__links_new[0][1]
        except IndexError:
            return self.__lastLinkLevel  # если нет новых ссылок - берем уровень последней ссылки

    def get_count_indexed_links(self):
        return len(self.__links_hash)

    def get_count_new_links(self):
        return len(self.__links_new)

    def __len__(self):
        return len(self.__links_hash)

