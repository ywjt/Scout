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
import datetime
import shutil
import commands
from base import ScoutBase, Loger
from base import CONF_DIR, LOGS_DIR, CACHE_DIR, PROC_DIR, PLUGIN_DIR
from base import cacheserver_running_alive



class CacheServerd(ScoutBase):
	def __init__(self):
		ScoutBase.__init__(self)
		__dbPath = '%s/.Scoutd/Bolt' % CACHE_DIR
		__logPath = '%s/cacheserver.log' % LOGS_DIR
		__storagePort = 6666
		__storageSize = self.avr['storage_size']
		if self.avr['storage_type'] in ['Memory','Disk']:
			if self.avr['storage_type']=='Memory':
				self.__CacheRunCommand = 'cacheServer \
										--port=%d \
										--dbpath=%s \
										--storageEngine=inMemory \
										--inMemorySizeGB=%d \
										--logpath=%s \
										--logappend \
										--fork \
										--quiet' % (__storagePort, __dbPath, __storageSize, __logPath)
			else:
				self.__CacheRunCommand = 'cacheServer \
										--port=%d \
										--dbpath=%s \
										--storageEngine=wiredTiger \
										--wiredTigerCacheSizeGB=%d \
										--logpath=%s \
										--logappend \
										--fork \
										--quiet' % (__storagePort, __dbPath, __storageSize, __logPath)
			self.__CacheStopCommand = 'cacheServer --dbpath=%s --shutdown' % __dbPath
		else:
			Loger().CRITICAL("'storage_type' value not match! options: 'Memory' or 'Disk'")
			raise

	def start(self):
		try:
			if not cacheserver_running_alive():
				os.chdir(PROC_DIR)
				status, output = commands.getstatusoutput(self.__CacheRunCommand)
				if status==0:
					Loger().INFO('CacheServer started with pid {}\n'.format(os.getpid()))
					time.sleep(2)
				else:
					Loger().ERROR('CacheServer started failed.')
			else:	
				Loger().INFO('CacheServer Daemon Alive!')
		except Exception as e:
			sys.stdout.write(str(e)+'\n')
			pass

	def stop(self):
		try:
			if cacheserver_running_alive():
				os.chdir(PROC_DIR)
				status, output = commands.getstatusoutput(self.__CacheStopCommand)
				if status==0:
					Loger().WARNING('CacheServer stop Success. {}\n'.format(time.ctime()))
					time.sleep(2)
				else:
					Loger().ERROR('CacheServer stop fail! %s' % output)
					raise
		except Exception as e:
			pass

	def restart(self):
		self.stop()
		self.start()



def initCache():
	__dbPath = '%s/.Scoutd/Bolt' % CACHE_DIR
	if os.path.exists(__dbPath):
		shutil.rmtree(__dbPath)
	os.system('mkdir -p %s' % __dbPath)
	os.chmod(__dbPath, 777)