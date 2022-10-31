from collections import deque
from imp import lock_held
import os
import shelve
import re
import time
from threading import Thread, RLock
from queue import Queue, Empty
from urllib.parse import urlparse

from utils import get_logger, get_urlhash, normalize
import scraper

class safeDequeue:
    def __init__(self, key):
        self.key = key
        self.rl = RLock()
        self.dq = deque()

class Frontier(object):
    #not thread safe, but should be fine
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded= list()
        for i in range(self.n):
            self.to_be_downloaded.append(safeDequeue(scraper.domains[i]))
        self.n = len(scraper.domains)
        self.saveLock = RLock()
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents- of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and scraper.is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")
    #thread safe
    def get_tbd_url(self):
        try:
            for i in range(self.n-1):
                if self.to_be_downloaded[i].rl.acquire(blocking=False) is True:
                    ret = self.to_be_downloaded[i].dq.pop()
                    self.to_be_downloaded[i].rl.release()
                    time.sleep(self.config.time_delay)
            self.to_be_downloaded[self.n-1].rl.acquire()
            ret = self.to_be_downloaded[self.n-1].dq.pop()
            self.to_be_downloaded[self.n-1].rl.release()
            return ret
        except IndexError:
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            self.saveLock.acquire()
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.saveLock.release()

            domain = urlparse(url).hostname
            for i in range(self.n-1):
                if re.match(r'.*' + self.to_be_downloaded[i].key +'$', domain):
                    self.to_be_downloaded[i].rl.acquire()
                    self.to_be_downloaded[i].dq.append(url)
                    self.to_be_downloaded[i].rl.release()
                
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")
        self.saveLock.acquire()
        self.save[urlhash] = (url, True)
        self.save.sync()
        self.saveLock.release()
