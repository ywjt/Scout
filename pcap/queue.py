#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
* @ Scout for Python
##############################################################################
# Author: YWJT / ZhiQiang Koo                                                #
# Modify: 2020-03-13                                                         #
##############################################################################
# This program is distributed under the "Artistic License" Agreement         #
# The LICENSE file is located in the same directory as this program. Please  #
# read the LICENSE file before you make copies or distribute this program    #
##############################################################################
"""

import sys
sys.path.append("..")
import os
import time
import psutil
import time
from threading import Thread
from multiprocessing import Process
from multiprocessing import Queue
from collections import deque
from cache.cache import CacheServer
from base import Loger
from base import ScoutBase


class PQueues(ScoutBase):

    def __init__(self):
        ScoutBase.__init__(self)
        self.TCP_DQ = deque(maxlen=500)
        self.UDP_DQ = deque(maxlen=500)

        """Instant a CacheServer
            exptime:
                expireAfterSeconds: <int> Used to create an expiring (TTL) collection. 
                MongoDB will automatically delete documents from this collection after <int> seconds. 
                The indexed field must be a UTC datetime or the data will not expire.
        """
        __Cache=CacheServer().create_or_connect_cache()
        self.TCP=__Cache["TCP"]
        self.UDP=__Cache["UDP"]
        CacheServer().create_index(self.TCP, "exptime", self.avr['expire_after_seconds'])
        CacheServer().create_index(self.UDP, "exptime", self.avr['expire_after_seconds'])

    def Qset(self, q=None):
        self.q = q

    def saveCache(self, bolt, stdout):
        try:
            obj = getattr(self, str(bolt))
            if type(stdout)==list:
                CacheServer().insert_many(obj, stdout)
            else:
                CacheServer().insert_one(obj, stdout)
        except Exception as e:
            Loger().ERROR("no collection name is %s, Error: %s" % (str(stdout["proto"]), str(e)))
            pass


    def Qpush(self, value):
        self.q.put(value)

    def Qdeque(self, dq, collection, value):
        if len(dq) == dq.maxlen:
            self.saveCache(collection, list(dq))
            dq.clear()
            time.sleep(0.1)
        dq.append(value)

    def Qsave(self):
        while 1:
            DQ=self.q.get()
            if DQ: 
                _dq_handle = getattr(self, "%s_DQ" % str(DQ["proto"]))
                self.Qdeque(_dq_handle, DQ["proto"], DQ)
            else:
                time.sleep(1)


    def createThread(self, func, *args):
        t = Thread(target=func, args=(args))
        t.start()
        return t

    def createProcess(self, func, *args):
        p = Process(target=func, args=(args))
        p.start()
        return p

