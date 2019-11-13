#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
* @ Scout for Python
##############################################################################
# Author: YWJT / ZhiQiang Koo                                                #
# Modify: 2019-11-13                                                        #
##############################################################################
# This program is distributed under the "Artistic License" Agreement         #
# The LICENSE file is located in the same directory as this program. Please  #
# read the LICENSE file before you make copies or distribute this program    #
##############################################################################
"""

import sys, os
sys.path.append("..")
import ConfigParser

CONF_DIR = '/etc/scout.d/'
LOGS_DIR = '/var/log/scout/'
CACHE_DIR = '/var/cache/'


try:
	f = open(CONF_DIR + "scoutd.conf", 'r')
	f.close()
except IOError as e:
	print("\"%s\" Config file not found." % CONF_DIR)
	sys.exit(1)

try:
	f = open(LOGS_DIR + "scoutd.pid", 'r')
	PID = f.read()
	f.close()
except IOError as e:
	print("Scout not running.")
	sys.exit(1)



"""
#==================================
# 加载配置文件内容
#==================================
"""
class LoadConfig(object):
	def __init__(self):
		self.cf = ConfigParser.ConfigParser()
		self.cf.read(CONF_DIR + "scoutd.conf")

	def getSectionValue(self, section, key):
		return self.getFormat(self.cf.get(section, key))

	def getSectionOptions(self, section):
		return self.cf.options(section)

	def getSectionItems(self, section):
		return self.cf.items(section)

	def getFormat(self, string):
		return string.strip("'").strip('"').replace(" ","")

LISTEN_IP = LoadConfig().getSectionValue('main','listen_ip').split(',')
