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
sys.path.append(".")
import os
import re
import string
import datetime
import time
from multiprocessing import Process
from base import async
from base import ScoutBase, Loger, Notes, Rules, Tailf
from base import scoutd_running_alive
from rule import Rule
from notice import PyEmail
from pcap.dstat import Dstat
from pcap.pkts import Pcapy
from plugin.jsonserver import app_run


class Scout(ScoutBase):
    def __init__(self):
        ScoutBase.__init__(self)
        cidr=self.cidr()
        self.kwargs={
            'interface': self.avr['motr_interface'],
            'filters': '{0} and {1} and {2}'.format(cidr['lip'], cidr['port'], cidr['wip']),
            'max_bytes': self.avr['max_bytes'],
            'promiscuous': self.avr['promiscuous'],
            'buffer_timeout': self.avr['buffer_timeout'],
            'expire_after_seconds': self.avr['expire_after_seconds'],
            'filepath':self.avr['file_path'], 
            'filetype': self.avr['file_type']
            }

    def echo(self, active='running', pid=os.getpid()):
        print('Scout v%s' % self.avr['version'])
        print('Active: \033[32m active (%s) \033[0m, PID: %d (Scoutd), Since %s' % (active, pid, time.strftime("%a %b %d %H:%M:%S CST", time.localtime())))
        print('Filter: (%s)' % self.kwargs['filters'])

    def status(self, pid):
        info=Dstat().process(pid)
        self.echo("running" if info["status"]=="sleeping" else "stoping", pid)
        info=sorted(info.iteritems(), key=lambda d:d[0], reverse=False) 
        for k, v in info:
            if k!="connections":
                print('%s : %s ' % (k, str(v)))

    def dstat(self):
        if scoutd_running_alive():
            Dstat().show()

    def view(self):
        if scoutd_running_alive():
            Rule().view()

    def tailf(self):
        if scoutd_running_alive():
            Tailf().follow()

    @async
    def async_dump(self):
        try:
            Pcapy().LOOP()
        except Exception as e:
            Loger().WARNING("Scout dump Exception: %s" %(e))
            raise


    @async
    def async_dstat(self):
        try:
            Dstat().LOOP()
        except Exception as e:
            Loger().WARNING("Scout dstat Exception: %s" %(e))
            pass


    @async
    def async_rule(self):
        try:
            Rule().LOOP()
        except Exception as e:
            Loger().WARNING("Scout rule Exception: %s" %(e))
            pass

    @async
    def async_plugin(self):
        try:
            app_run()
        except Exception as e:
            Loger().WARNING("ScoutHttpApi Exception: %s" %(e))
            pass



    def run(self):
        self.async_dump()
        self.async_rule()
        self.async_dstat()
        self.async_plugin()
        self.echo()



