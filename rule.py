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
import subprocess
from threading import Thread
from prettytable import PrettyTable
from time import sleep
from notice import PyEmail
from base import async
from cache.cache import CacheServer
from base import ScoutBase, Loger, Notes, Rules, async
from base import CONF_DIR, LOGS_DIR, CACHE_DIR


class Rule(ScoutBase):

	def __init__(self):
		ScoutBase.__init__(self)
		self.filepath = self.avr['file_path'] if self.avr['file_path'] else CONF_DIR+"/rules"
		self.filetype = self.avr['file_type'] if self.avr['file_type']=='yaml' else 'json'
		self.S = {}

		"""Instant a CacheServer
		"""
		self.Cache = CacheServer().create_or_connect_cache()
		self.Bcol = self.Cache["BLOCK"]
		CacheServer().create_index(self.Bcol, "_id")


	def cache_connect(self, bolt):
		return self.Cache[CacheServer().get_collection(self.Cache, bolt)]

	
	def load_cache(self, collection, condition, stdout):
		return CacheServer().replace_id(collection, condition, stdout)


	"""
		存储配置文件解析后的key==>value键值对
		为了减轻loop过程中每次打开配置文件的IO线程。
		这里仅仅用了一个类的全局对象，如果配置文件发生变更，则不会实时读取，需要重启进程。
	"""
	def rule_key_value(self, basename):
		if basename:
			self.S[basename] = Rules(basename).echo()
	

	"""
		封锁操作
		confname:
			配置文件名，在数据记录里会登记属于哪些配置所触发的记录
		parse:
			解析后的配置文件的字典集
		data:
			通过filter查询返回的结果集
	"""
	def rule_block(self, confname, parse={}, data={}):
		# 输出符合过滤条件的信息
		Loger().WARNING("[%s] %s" % (confname, data))

		# 解析block，注意配置文件不能缺少关键字
		try:
			action = parse['block']['action']
			expire = parse['block']['expire']
			command = parse['block']['blkcmd']
			iptables = parse['block']['iptables']
		except Exception as e:
			Loger().ERROR("block rule farmat error.")
			raise

		block_data={}
		block_data['_id'] = data['_id']
		block_data['total'] = data['total']
		block_data["time"]=int(time.time())
		block_data["exptime"]=int(time.time()) + expire
		block_data["confname"]=str(confname)
		block_data["command"]=''

		if action:
			if iptables:
				block_data["command"] = ("/sbin/iptables -I INPUT -s %s -j DROP" % data['_id'])
			else: 
				if command.find(' %s')>0:
					data['block']=1
					block_data["command"] = (command % data)

			state=self.load_cache(self.Bcol, {'_id': data['_id']}, block_data)
			if state:
				subprocess.call(block_data["command"], shell=True)
				Loger().WARNING(Notes['LOCK'] % (data['_id'], data['total']))
				#发出邮件通知
				self.rule_notice(confname, parse, data)
		else:
			Loger().WARNING(Notes['RECORD'] % (data['_id'], data['total']))


	"""
		解锁操作
		confname:
			配置文件名，在数据记录里会登记属于哪些配置所触发的记录
		parse:
			解析后的配置文件的字典集
	"""
	@async
	def rule_unblock(self, confname, parse={}):
		# 解析block，注意配置文件不能缺少关键字
		try:
			action = parse['block']['action']
			expire = parse['block']['expire']
			command = parse['block']['ubkcmd']
			iptables = parse['block']['iptables']
		except Exception as e:
			Loger().ERROR("block rule farmat error.")
			raise

		if action:
			#解封过时记录
			call_cmd=''
			kwargs={'exptime': {'$lt': int(time.time())}, 'confname': confname}
			for item in CacheServer().find_conditions(self.Bcol, **kwargs):
				if iptables:
					call_cmd=("/sbin/iptables -D INPUT -s %s -j DROP" % item['_id'])
				else:
					if command.find(' %s')>0:
						temp={}
						temp['_id']=item['_id']
						temp['total']=item['total']
						temp['unblock']=1
						call_cmd=(command % temp)

				subprocess.call(call_cmd, shell=True)
				Loger().WARNING(Notes['UNLOCK'] % item['_id'])

			CacheServer().delete_many(self.Bcol, kwargs)


	def rule_notice(self, confname, parse={}, data={}):
		try:
			send = parse['notice']['send']
			email = parse['notice']['email']
		except Exception as e:
			Loger().ERROR("block rule farmat error.")
			raise

		subject = "Scout email server"
		if send:
			for receiver in email:
				PyEmail().sendto(subject, Notes['MAIL'] %(data['_id'], confname, data['total']), receiver)


	"""
		主要解析函数
		解析配置filter部份，并查询结果。

		return: 
	 		结果集 {u'total': 101, u'_id': u'1.1.1.1'}
		basename:
			配置文件名
		parse:
			已解析过的字典(缓存里的数据)
			
	"""
	def rule_filter(self, parse={}):

		if parse['bolt'] in ["TCP", "UDP"]:
			col = self.cache_connect(parse['bolt'])
		else:
			Loger().ERROR("Bolt value must be 'TCP', 'UDP' !")
			raise

		# 解析filter，注意配置文件不能缺少关键字
		try:
			timeDelta =       parse['filter']['timeDelta']  #时间区间, Seconds.
			trustIps =        parse['filter']['trustIps']   #排除src白名单
			motrPort =        parse['filter']['motrPort']   #过滤端口
			motrProto =       parse['filter']['motrProto']  #过滤协议
			flags =           parse['filter']['flags']      #连接状态
			noOfConnections = parse['filter']['noOfConnections'] #阀值
			noOfCondition =   parse['filter']['noOfCondition']   #阀值条件 如$ge\$gt\$gte\$lt\$lte
			returnFiled =     parse['filter']['returnFiled']     #过滤器返回的字段名, blot表里必须存在
		except Exception as e:
			Loger().ERROR("filter rule farmat error.")
			raise

		#构造查询
		aggs=[]
		lte_time = int(time.time())
		gte_time = (lte_time - timeDelta)
		if timeDelta: aggs.append({'$match': {'time' : {'$gte' : gte_time, '$lte' : lte_time}}})
		if flags:     aggs.append({'$match': {'flags': {'$in': flags}}})
		if motrPort:  aggs.append({'$match': {'dport': {'$in': motrPort}}})
		if trustIps:  aggs.append({'$match': {'src': {'$nin': trustIps}}})
		aggs.append({'$group': {'_id': '$%s' %returnFiled, 'total': {'$sum': 1}}})
		aggs.append({'$match': {'total': {noOfCondition: noOfConnections}}})

		#Loger().DEBUG(aggs)
		return CacheServer().find_aggregate(col, aggs)

	"""
		查看封锁记录
	"""
	def view(self):
		__lineRows = False
		table = PrettyTable(['_ID','ConfName','Total','Command','Time'])
		kwargs={'exptime': {'$gte': int(time.time())}}
		for item in CacheServer().find_conditions(self.Bcol, **kwargs):
			table.add_row([item['_id'], item['confname'], item['total'], item['command'], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['time']))])
			__lineRows = True

		if __lineRows:  table.sort_key(item['time'])
		table.reversesort=False
		table.border = 1
		print(table)


	def LOOP(self, keeprunning=True, timeout=1):
		while keeprunning:
			"""如果缓存里有key==>value
			   则取缓存数据,否则重新加载配置文件
			"""
			if self.S:
				for k in self.S.keys():
					#执行解锁
					self.rule_unblock(k, self.S[k])
					#执行封锁
					for res in self.rule_filter(self.S[k]):
						self.rule_block(k, self.S[k], res)
						Loger().WARNING("[%s.%s] %s" % (k, self.filetype, res))
			else:
				ptn = re.compile('.*\.%s' % self.filetype)
				for f in os.listdir(self.filepath):
					ff = ptn.match(f)
					if not ff is None:
						tp = ff.group().split('.')[0]
						self.rule_key_value(tp)

			sleep(timeout)



