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
import os
sys.path.append(".")
import os
import ConfigParser
import functools
import threading
import logging
import yaml
import datetime
import time
from time import sleep
from signal import SIGTERM
from __init__ import __VERSIONS__
try:
    import cPickle as pickle
except ImportError:
    import pickle

CONF_DIR = '/etc/scout.d/'
LOGS_DIR = '/var/log/scout/'
CACHE_DIR = '/var/cache/'
PROC_DIR =  '/usr/local/scout/'
PLUGIN_DIR = PROC_DIR+'plugin/'
PCAP_ID_FILE = '%s/.__pcap.id' % LOGS_DIR

if not os.path.exists(PROC_DIR):
	print("run path failed: %s \n" % PROC_DIR)
	sys.exit(1)

if not os.path.exists(LOGS_DIR):
	os.system('mkdir -p %s' %LOGS_DIR)
	os.chmod(LOGS_DIR, 775)


def save_pid(bytes_text):
	try:
		f = open(PCAP_ID_FILE, 'wb+')
		pickle.dump(bytes_text, f)
		f.close()
	except IOError as e:
		Loger().ERROR('%s not found!' % PCAP_ID_FILE)

def del_pid():
	try:
		f = file(PCAP_ID_FILE, 'r')
		pids = pickle.load(f)
		for pid in pids:
			os.kill(int(pid), SIGTERM)
		f.close()
		os.remove(PCAP_ID_FILE)
	except IOError as e:
		print("del pid #1 failed: %d (%s)\n" % (e.errno, e.strerror))
		sys.exit(1)

def cacheserver_running_alive():
	cache = os.popen('ps -fe|grep "cacheServer"|grep -v "grep"|wc -l').read().strip()
	if (cache == '0'):
		return None
	else:
		return True

def scoutd_running_alive():
	try:
		f = open(LOGS_DIR + "scoutd.pid", 'r')
		PID = f.read()
		f.close()
		return True
	except IOError as e:
		Loger().STDOUT()
		Loger().ERROR('Scoutd not running... you must be start it first!')
		sys.exit(1)


"""
#==================================
# 异步修饰
#==================================
"""
def async(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
		my_thread.start()
	return wrapper


"""
#==================================
# 加载配置文件内容
#==================================
"""
class LoadConfig(object):
	cf = ''
	filepath = CONF_DIR + "scoutd.conf"

	def __init__(self):
		try:
			f = open(self.filepath, 'r')
		except IOError as e:
			print("\"%s\" Config file not found." % (self.filepath))
			sys.exit(1)
		f.close()

		self.cf = ConfigParser.ConfigParser()
		self.cf.read(self.filepath)

	def getSectionValue(self, section, key):
		return self.getFormat(self.cf.get(section, key))
	def getSectionOptions(self, section):
		return self.cf.options(section)
	def getSectionItems(self, section):
		return self.cf.items(section)
	def getFormat(self, string):
		return string.strip("'").strip('"').replace(" ","")


"""
#==================================
# 初始化主类参数，用于后续继承
#==================================
"""
class ScoutBase(object):
	avr = {}
	avr['version'] = __VERSIONS__ if __VERSIONS__ else 'none'

	def __init__(self):
		self.avr['log_level'] = LoadConfig().getSectionValue('system', 'log_level')
		self.avr['log_file'] = LoadConfig().getSectionValue('system', 'log_file')
		self.avr['listen_ip'] = LoadConfig().getSectionValue('main','listen_ip')
		self.avr['trust_ip'] = LoadConfig().getSectionValue('main','trust_ip')
		self.avr['motr_port'] = LoadConfig().getSectionValue('main','motr_port')
		self.avr['motr_interface'] = LoadConfig().getSectionValue('main','motr_interface')
		self.avr['max_bytes'] = int(LoadConfig().getSectionValue('main','max_bytes'))
		self.avr['promiscuous'] = bool(LoadConfig().getSectionValue('main','promiscuous'))
		self.avr['buffer_timeout'] = int(LoadConfig().getSectionValue('main','buffer_timeout'))
		self.avr['expire_after_seconds'] = int(LoadConfig().getSectionValue('cache','expire_after_seconds'))
		self.avr['storage_type'] = LoadConfig().getSectionValue('cache','storage_type')
		self.avr['storage_size'] = int(LoadConfig().getSectionValue('cache','storage_size'))
		self.avr['file_path'] = LoadConfig().getSectionValue('rules','file_path')
		self.avr['file_type'] = LoadConfig().getSectionValue('rules','file_type')
		self.avr['admin_email'] = LoadConfig().getSectionValue('alert','admin_email')
		self.avr['smtp_server']= LoadConfig().getSectionValue('alert','smtp_server')
		self.avr['admin_email'] = LoadConfig().getSectionValue('alert','admin_email')
		self.avr['smtp_user'] = LoadConfig().getSectionValue('alert','smtp_user')
		self.avr['smtp_passwd'] = LoadConfig().getSectionValue('alert','smtp_passwd')
		self.avr['smtp_ssl'] = LoadConfig().getSectionValue('alert','smtp_ssl')
		self.avr['http_host'] = LoadConfig().getSectionValue('http','http_host')
		self.avr['http_port'] = LoadConfig().getSectionValue('http','http_port')

	def getValue(self):
		return self.var


	def cidr(self):
		s = {}
		s['wip']=''
		s['port']=''
		s['lip']=''
		for locip in self.avr['listen_ip'].split(","):
			if locip:
				s['lip'] += 'dst host {0} or '.format(locip)
		for port in self.avr['motr_port'].split(","):
			if port:
				s['port'] += 'dst port {0} or '.format(port)
		for wip in self.avr['trust_ip'].split(","):
			if wip:
				if wip.find("~")>0:
					lstart = int(wip.split("~")[0].split(".")[-1])
					lend = int(wip.split("~")[1].split(".")[-1])+1
					ldun = ".".join(wip.split("~")[1].split(".")[0:3])
					for wli in xrange(lstart, lend):
						s['wip'] += '! dst net {0} and '.format("%s.%d" % (ldun,wli))
				elif wip.find("-")>0:
					lstart = int(wip.split("-")[0].split(".")[-1])
					lend = int(wip.split("-")[1].split(".")[-1])+1
					ldun = ".".join(wip.split("-")[1].split(".")[0:3])
					for wli in xrange(lstart, lend):
						s['wip'] += '! dst net {0} and '.format("%s.%d" % (ldun,wli))
				else:
					s['wip'] += '! dst net {0} and '.format(wip)
		s['lip'] = s['lip'].strip('or ')
		s['port']= s['port'].strip('or ')
		s['wip'] = s['wip'].strip('and ')
		return s


"""
#==================================
# 加载rules文件内容
#==================================
"""
class Rules(ScoutBase):
	def __init__(self, basename):
		ScoutBase.__init__(self)

		if self.avr['file_path']:
			filepath = '%s/%s' %(self.avr['file_path'], basename)
		else:
			filepath = '%s/%s' %(CONF_DIR+"/rules", basename)

		if self.avr['file_type'] == 'yaml':
			self.parse = self.YAML(self.FILE(filepath, self.avr['file_type']))
		elif self.avr['file_type'] == '' or self.avr['file_type'] == 'json':
			self.parse = self.JSON(self.FILE(filepath, 'json'))
		else:
			Loger().ERROR("rules file type not Supportd!")
			raise

	def echo(self):
		return self.parse

	def FILE(self, filepath, filetype):
		return "%s.%s" %(filepath, filetype)

	def YAML(self, filename):
		with open(filename, 'r') as f:
			yam = yaml.load(f.read())
		return yam

	def JSON(self, filename):
		with open(filename, 'r') as f:
			js = json.loads(f.read())
		return js



"""
#==================================
# 日志记录方法
#==================================
"""
class Loger(ScoutBase):
	def __init__(self):
		ScoutBase.__init__(self)

		if self.avr['log_file'].find("/") == -1:
			self.log_file = LOGS_DIR + self.avr['log_file']
		else:
			self.log_file = self.avr['log_file']

		if self.avr['log_level'].upper()=="DEBUG":
			logging_level = logging.DEBUG
		elif self.avr['log_level'].upper()=="INFO":
			logging_level = logging.INFO
		elif self.avr['log_level'].upper()=="WARNING":
			logging_level = logging.WARNING
		elif self.avr['log_level'].upper()=="ERROR":
			logging_level = logging.ERROR
		elif self.avr['log_level'].upper()=="CRITICAL":
			logging_level = logging.CRITICAL
		else:
			logging_level = logging.WARNING

		logging.basicConfig(level=logging_level, 
                    format='%(asctime)s %(levelname)s %(message)s', # 日志格式
                    datefmt='%Y-%m-%d %H:%M:%S', # 时间格式：2018-11-12 23:50:21
                    filename=self.log_file, # 日志的输出路径
                    filemode='a')  # 追加模式

	def STDOUT(self):
		logger = logging.getLogger()
		ch = logging.StreamHandler()
		logger.addHandler(ch)
	def DEBUG(self, data):
		return logging.debug(data)
	def INFO(self, data):
		return logging.info(data)
	def WARNING(self, data):
		return logging.warning(data)
	def ERROR(self, data):
		return logging.error(data)
	def CRITICAL(self, data):
		return logging.critical(data)


"""
#==================================
# 日志监听输出
#==================================
"""
class Tailf(ScoutBase):
	def __init__(self):
		ScoutBase.__init__(self)
		__logfilename = LOGS_DIR + self.avr['log_file']
		self.check_file_validity(__logfilename)
		self.tailed_file = __logfilename
		self.callback = sys.stdout.write
 
	def follow(self, s=1):
		print("logging output ......")
		with open(self.tailed_file) as file_:
			file_.seek(0, 2)
			while True:
				curr_position = file_.tell()
				line = file_.readline()
				if not line:
					file_.seek(curr_position)
				else:
					self.callback(line)
				time.sleep(s)
 
	def register_callback(self, func):
		self.callback = func
 
	def check_file_validity(self, file_):
		if not os.access(file_, os.F_OK):
			raise TailError("File '%s' does not exist" % (file_))
		if not os.access(file_, os.R_OK):
			raise TailError("File '%s' not readable" % (file_))
		if os.path.isdir(file_):
			raise TailError("File '%s' is a directory" % (file_))
 
class TailError(Exception):
	def __init__(self, msg):
		self.message = msg
	def __str__(self):
		return self.message


"""
#==================================
# 日志记录类型
#==================================
# [RECORD]   非封锁记录
# [LOCK]     封锁
# [UNLOCK]   解封
# [REBL]     重载封锁列表
# [MAIL]     发送邮件
#==================================
"""
Notes = {
	"RECORD" : "[RECORD] %s has been Unusual, It has %s packets transmitted to server.",
	"LOCK" : "[LOCK] %s has been blocked, It has %s packets transmitted to server.",
	"UNLOCK": "[UNLOCK] %s has been unblocked.",
	"REBL": "[REBL] %s reload in iptables Success.",
	"MAIL": "[MAIL] %s record on %s,It has %s packets transmitted to server. Attention please!"
}






