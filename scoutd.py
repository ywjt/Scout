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
import time
import atexit
import datetime
import commands
import shutil
import platform
import signal
from signal import SIGTERM
from base import ScoutBase, Loger, del_pid
from base import CONF_DIR, LOGS_DIR, CACHE_DIR, PROC_DIR, PLUGIN_DIR
from base import cacheserver_running_alive, scoutd_running_alive
from util import Scout
from pcap.dstat import Dstat
from cache.cacheserver import CacheServerd, initCache


class Daemon:
	"""
	daemon class.	
	Usage: subclass the Daemon class and override the _run() method
	"""
	def __init__(self, pidfile='/tmp/daemon.pid', stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = LOGS_DIR + pidfile
		self.chdir = PROC_DIR
	
	def _daemonize(self):
		#脱离父进程
		try: 
			pid = os.fork() 
			if pid > 0:
				sys.exit(0) 
		except OSError as e: 
			Loger().ERROR("Scoutd fork #1 failed:"+str(e.strerror))
			sys.exit(1)
		os.setsid() 
		os.chdir(self.chdir) 
		os.umask(0)
	
		#第二次fork，禁止进程重新打开控制终端
		try: 
			pid = os.fork() 
			if pid > 0:
				sys.exit(0) 
		except OSError as e: 
			Loger().ERROR("Scoutd fork #2 failed:"+str(e.strerror))
			sys.exit(1) 

		sys.stdout.flush()
		sys.stderr.flush()
		si = file(self.stdin, 'r')
		so = file(self.stdout, 'a+')
		se = file(self.stderr, 'a+', 0) 
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write("%s\n" % pid)
	
	def delpid(self):
		os.remove(self.pidfile)

	def start(self):
		"""
		Start the daemon
		"""
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError as e:
			pid = None
	
		if pid:
			message = "Start error,pidfile %s already exist. Scoutd already running?"
			Loger().ERROR(message % self.pidfile)
			sys.exit(1)

		self._daemonize()
		self._run()

	def stop(self):
		"""
		Stop the daemon
		"""
		self._stop_first()

		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError as e:
			pid = None
	
		if not pid:
			message = "pidfile %s does not exist. Scoutd not running?"
			Loger().ERROR(message % self.pidfile)
			return

		try:
			while 1:
				os.kill(pid, SIGTERM)
				time.sleep(0.1)
		except OSError as err:
			err = str(err)
			if err.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
					Loger().WARNING("stop Scoutd Success.")
			else:
				Loger().ERROR("stop error,"+str(err))
				sys.exit(1)


	def restart(self):
		self.stop()
		self.start()


class Scoutd(Daemon):
	def status(self):
		try:
			pf = file(self.pidfile, 'r')
			pid = int(pf.read().strip())
			pf.close()
			Scout().status(pid)
		except IOError as e:
			message = "No such a process running.\n"
			sys.stderr.write(message)


	def _run(self):
		if not cacheserver_running_alive():
			Loger().ERROR('CacheServer not running... you must be start it first!')
			sys.exit(1)
		Loger().INFO('Scoutd %s ' % ScoutBase().avr['version'])
		Loger().INFO('Copyright (C) 2011-2019, YWJT.org.')
		Loger().INFO('Scoutd started with pid %d' % os.getpid())
		Loger().INFO('Scoutd started with %s' % datetime.datetime.now().strftime("%m/%d/%Y %H:%M"))
		Scout().run()

	def _stop_first(self):
		del_pid()




def help():
	__MAN = 'Usage: %s \n \
		          \n \
Options:  \n \
	init       creating and initializing a new cache partition. \n \
	start      start all service. \n \
	stop       stop main proccess, cacheserver keep running. \n \
	restart    restart main proccess, cacheserver keep running. \n \
	reload     same as restart. \n \
	forcestop  stop all service, include cacheserver and main proccess. \n \
	reservice  restart cacheserver and main proccess. \n \
	status     show main proccess run infomation. \n \
	dstat      show generating system resource statistics. \n \
	view       check block/unblock infomation. \n \
	watch      same as tailf, watching log output. \n \
	help       show this usage information. \n \
	version    show version information. \n \
	'
	print(__MAN % sys.argv[0])


if __name__ == '__main__':
	cached = CacheServerd()
	scoutd = Scoutd(pidfile='scoutd.pid')

	if len(sys.argv) > 1:
		if 'START' == (sys.argv[1]).upper():
			cached.start()
			scoutd.start()
		elif 'STOP' == (sys.argv[1]).upper():
			scoutd.stop()
		elif 'FORCESTOP' == (sys.argv[1]).upper():
			scoutd.stop()
			cached.stop()
		elif 'RESERVICE' == (sys.argv[1]).upper():
			print("Are you sure force restart Scoutd service?\n \
  When the cacheServer is restarted, \n \
    * If you set storage_type = 'Memory', the data records will be cleared.\n \
    * If you set storage_type = 'Disk', the data records not be cleared.")
			if raw_input("Enter ('yes|y|Y'):") in ['yes', 'Y', 'y']:
				cached.restart()
				scoutd.restart()
		elif 'RESTART' == sys.argv[1].upper():
			scoutd.restart()
		elif 'RELOAD' == sys.argv[1].upper():
			scoutd.restart()
		elif 'STATUS' == (sys.argv[1]).upper():
			scoutd.status()
		elif 'HELP' == (sys.argv[1]).upper():
			help()
		elif 'WATCH' == (sys.argv[1]).upper():
			Scout().tailf()
		elif 'VERSION' == (sys.argv[1]).upper():
			print(ScoutBase().avr['version'])
		elif 'VIEW' == (sys.argv[1]).upper():
			Scout().view()
		elif 'INIT' == (sys.argv[1]).upper():
			print("Are you sure initialize Scoutd service?\n When the cache data will be cleared.")
			if raw_input("Enter ('yes|y|Y'):") in ['yes', 'Y', 'y']:
				cached.stop()
				initCache()
				cached.start()
		elif 'DSTAT' == (sys.argv[1]).upper():
			Scout().dstat()
		else:
			print "Unknow Command!"
			help()
			sys.exit(1)
	else:
		print(ScoutBase().avr['version'])
		help()
		sys.exit(1)
