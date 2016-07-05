# -*- coding: utf-8 -*-
from datetime import datetime, date
import calendar


def calendar_line(data_begin, count_days, group_by_month=False):
    year = data_begin.year
    month = data_begin.month
    day = data_begin.day
    count_days_per_month = calendar.monthrange(year, month)[1]
    result = []
    days = []
    while count_days > 0:
        count_days -= 1
        if group_by_month:
            days.append(date(year, month, day))
        else:
            result.append(date(year, month, day))
        day += 1
        if day > count_days_per_month or count_days < 1:
            day = 1
            month += 1
            if group_by_month:
                result.append(days)
                days = []
            if month > 12:
                month = 1
                year += 1
            count_days_per_month = calendar.monthrange(year, month)[1]
    return result

if __name__ == '__main__':
    print '==============================='
    d = calendar_line(datetime(2015, 2, 3), 45, True)
    print d
    print '==============================='
    for elm in d:
        print elm
    print '==============================='
