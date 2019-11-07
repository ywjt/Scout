#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
* @ Scout for Python
##############################################################################
# Author: YWJT / ZhiQiang Koo                                                #
# Modify: 2019-11-06                                                         #
##############################################################################
# This program is distributed under the "Artistic License" Agreement         #
# The LICENSE file is located in the same directory as this program. Please  #
# read the LICENSE file before you make copies or distribute this program    #
##############################################################################
"""

import sys
sys.path.append("..")
import os, sys, re
import string
import datetime, time
from lib.notice import PyEmail
from lib.dstat import Dstat
from lib import async
from lib import Dshield, Loger, Notes, Rules
from lib.pkts import Pcapy
from lib.rule import Rule


class Scout(Dshield):
    def __init__(self):
        Dshield.__init__(self)
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
            if k=="connections":
                print('%s : ' % k)
                for l in v:
                    print('     --| %s' % str(l))
            else:
                print('%s : %s ' % (k, str(v)))

    def dstat(self):
        try:
            Dstat().show()
        except Exception as e:
            Loger().WARNING("Scout dstat Exception: %s" %(e))
            pass

    def view(self):
        try:
            Rule(**self.kwargs).view()
        except Exception as e:
            Loger().WARNING("Scout rule Exception: %s" %(e))
            pass


    @async
    def async_dump(self):
        try:
            Pcapy(**self.kwargs).DUMP()
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
            Rule(**self.kwargs).LOOP()
        except Exception as e:
            Loger().WARNING("Scout rule Exception: %s" %(e))
            pass



    def run(self):
        self.async_dump()
        self.async_rule()
        self.async_dstat()
        self.echo()

