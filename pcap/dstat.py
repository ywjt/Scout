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
import re
import time
import datetime
import psutil
from time import sleep
from base import ScoutBase
from cache.cache import CacheServer
from base import async, Loger
from prettytable import PrettyTable


class Dstat(ScoutBase):

	def __init__(self):
		ScoutBase.__init__(self)

		"""Instant a CacheServer
		"""
		self.Cache = CacheServer().create_or_connect_cache()
		self.Dcol = self.Cache["DSTAT"]
		CacheServer().create_index(self.Dcol, "exptime", self.avr['expire_after_seconds'])


	def load_cache(self, collection_obj, stdout):
		CacheServer().insert_one(collection_obj, stdout)


	def show(self):
		__lineRows = False
		table = PrettyTable(['Time','1min','5min','15min','%CPU','MemFree(MiB)','Recv(MiB)','Send(MiB)'])
		kwargs={'time': {'$gte': int(time.time()-900)}}
		for item in CacheServer().find_conditions(self.Dcol, **kwargs):
			table.add_row([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['time'])), item['1m'], item['5m'], item['15m'], item['cpu_percent'], item['mem_free'], item['recv'], item['send']])
			__lineRows = True
		if __lineRows: table.sort_key(item['time'])
		table.reversesort=False
		table.border = 1
		print(table)


	def net_io_counters(self):
		net_io = psutil.net_io_counters(pernic=True)
		recv = net_io[self.avr['motr_interface']].bytes_recv
		send = net_io[self.avr['motr_interface']].bytes_sent
		return (float(recv), float(send))
	  
	def cpu_count(self, logical=False):
		"""
		logical 显示物理cpu数还是逻辑个数
		"""
		return psutil.cpu_count(logical)

	def cpu_times_idle(self, interval=1, percpu=False):
		idle=[]
		for c in psutil.cpu_times_percent(interval, percpu):
			idle.append(c.idle)
		return idle
	
	def cpu_percent(self, interval=1, percpu=False):
		"""
		interval 计算cpu使用率的时间间隔
		percpu   选择总的使用率还是每个cpu的使用率
		"""
		return psutil.cpu_percent(interval, percpu)

	def memory_info(self):
		mem = psutil.virtual_memory()
		total = "%d" %(mem.total/1024/1024)
		free = "%d" %(mem.available/1024/1024)
		return (total, free)

	def process(self, pid):
		proc_info={}
		p = psutil.Process(pid)
		proc_info["name"]=p.name()        #进程名
		proc_info["exe"]=p.exe()         #进程的bin路径
		proc_info["cwd"]=p.cwd()         #进程的工作目录绝对路径
		proc_info["status"]=p.status()      #进程状态
		proc_info["create_time"]=p.create_time()  #进程创建时间
		proc_info["running_time"]='%d Seconds' % int((time.time()-proc_info["create_time"]))
		proc_info["uids"]=p.uids()          #进程uid信息
		proc_info["gids"]=p.gids()           #进程的gid信息
		proc_info["cpu_times"]=p.cpu_times()      #进程的cpu时间信息,包括user,system两个cpu信息
		proc_info["cpu_affinity"]=p.cpu_affinity()   #get进程cpu亲和度,如果要设置cpu亲和度,将cpu号作为参考就好
		proc_info["memory_percent"]=p.memory_percent() #进程内存利用率
		proc_info["memory_info"]=p.memory_info()    #进程内存rss,vms信息
		proc_info["io_counters"]=p.io_counters()    #进程的IO信息,包括读写IO数字及参数
		proc_info["connections"]=p.connections()    #返回进程列表
		proc_info["num_threads"]=p.num_threads()  #进程开启的线程数
		return proc_info


	def net(self):
		net = {}
		(recv, send) = self.net_io_counters()
		while True:  
			time.sleep(2)
			(new_recv, new_send) = self.net_io_counters() 
			net['recv'] = "%.3f" %((new_recv - recv)/1024/1024)
			net['send'] = "%.3f" %((new_send - send)/1024/1024)
			return net


	def loadavg(self):
		loadavg = {}
		f = open("/proc/loadavg","r")
		con = f.read().split()
		f.close()
		loadavg['1m'] = con[0]
		loadavg['5m'] = con[1]
		loadavg['15m'] = con[2] 
		return loadavg

	def LOOP(self, keeprunning=True, timeout=60):
		data ={}
		while keeprunning:
			data = dict(self.net(), **self.loadavg())
			#data["time"]=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
			data["time"]=int(time.time())
			data["exptime"]=datetime.datetime.utcnow()
			data["cpu_percent"]=self.cpu_percent()
			data["mem_total"],data["mem_free"] =self.memory_info()
			data["cpu_physics"] = self.cpu_count(1)
			data["cpu_logical"] = self.cpu_count()

			#Loger().INFO(data)
			self.load_cache(self.Dcol, data)
			sleep(timeout)









