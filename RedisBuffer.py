# -*- coding: utf-8 -*-
import pickle
from redis import StrictRedis
import time

# http://devacademy.ru/posts/vvedenie-v-redis-py/

DEFAULT_STORAGE_TIME = 7*24*60*60
# очередь на основе Redis
class RedisBuffer(object):
    def __init__(self, name, storage_time=None):
        self.name = '_buff_'+name
        if storage_time is None: storage_time = DEFAULT_STORAGE_TIME
        self.storage_time = storage_time

    def set_storage_time(self, new_time_interval):
        self.storage_time = new_time_interval

    def connection(self):
        return StrictRedis(host="localhost", port=6379, db=2)

    def set(self, **kwargs):
        redis = self.connection()
        for key, value in kwargs.items():
            key = self.name +'_'+ key
            redis.setex(name=key, value=pickle.dumps(value), time=self.storage_time)

    def get(self, key, default=None):
        key = self.name +'_'+ key
        result = self.connection().get(key)
        if result is None:
            return default
        return pickle.loads(result)

