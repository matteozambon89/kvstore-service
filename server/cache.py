import os
import time
import hashlib
from os import path
from pickle import dumps, loads

from werkzeug import secure_filename


class FileSystemCache:
    def __init__(self, cache_root):
        self.cache_root = cache_root

    def get_cache_path_for(self, key):
        hasher = hashlib.sha256()
        hasher.update(key)
        key = hasher.hexdigest()
        cache_path = path.join(self.cache_root, str(key.__hash__())[-2:])
        if not path.exists(cache_path):
            os.makedirs(cache_path)
        return path.join(cache_path, secure_filename(key))

    def cache(self, key, data, expiration):
        # expiration comes in as ms, so convert to seconds and 
        # add to the current time
        expiration_time = int(expiration + time.time())
        with open(self.get_cache_path_for(key), "w") as f:
            f.write("%d\n" % expiration_time)
            f.write(dumps(data))

    def read_from_cache(self, key, factory_method=None):
        try:
            with open(self.get_cache_path_for(key), "r") as f:
                expiration = int(f.readline())
                # if the cached item is expired, return None
                if expiration < time.time():
                    if factory_method:
                        return (False, factory_method())
                    else:
                        return (False, None)
                return (expiration, loads(f.read()))
        except IOError as e:
            # this is generally because the item isn't there
            return (False, factory_method())

    def get_or_return_from_cache(self, key, expiration, factory_method, force_refresh=False):
        if force_refresh:
            item = (False, factory_method())
        else:
            item = self.read_from_cache(key, factory_method)
        self.cache(key, item[1], expiration)
        return item
