#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
* @ Scout for Python
##############################################################################
# Author: YWJT / ZhiQiang Koo                                                #
# Modify: 2019-11-13                                                         #
##############################################################################
# This program is distributed under the "Artistic License" Agreement         #
# The LICENSE file is located in the same directory as this program. Please  #
# read the LICENSE file before you make copies or distribute this program    #
##############################################################################
"""


import sys
sys.path.append("..")
import os, sys
import time
import psutil
from calendar import timegm
from datetime import datetime
from base import ScoutBase
from cache.cache import CacheServer

_LISTEN_IP = ScoutBase().avr['listen_ip'].split(',')


def convert_to_time_ms(timestamp):
    return 1000 * timegm(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple())

def convert_time_ms_agg(timestamp):
    return timegm(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple())


class GetSeries(object):
    def __init__(self):
        self.Cache = CacheServer().create_or_connect_cache()
        self.TCPcol=self.Cache["TCP"]
        self.UDPcol=self.Cache["UDP"]
        self.Dcol = self.Cache["DSTAT"]
        self.Bcol = self.Cache["BLOCK"]

    def data_series_uptime(self,req, pid):
        """
        运行时间
        """
        p = psutil.Process(pid)
        times = int(time.time()-p.create_time())
        return [{ 
            "target": "uptime", 
            "datapoints": [
                    [times, convert_to_time_ms(req['range']['from'])], 
                    [times, convert_to_time_ms(req['range']['to'])]
                ]
            }]

    def data_series_cpu_percent(self,req):
        """
        CPU使用率
        """
        kw = {"time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.Dcol, limit=500, **kw)
        _cpu = []
        for res in get_series:
            if not res is None: _cpu.append([float(res['cpu_percent']), int(res["time"]*1000)])
        return [{ "target": "cpu_percent", "datapoints": _cpu}]

    def data_series_load_average(self,req):
        """
        当前负载
        """
        kw = {"time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.Dcol, limit=500, **kw)
        _1m=[]
        _5m=[]
        _15m=[]
        for res in get_series:
            if not res is None:
                _1m.append([res['1m'], int(res["time"]*1000)])
                _5m.append([res['5m'], int(res["time"]*1000)])
                _15m.append([res['15m'], int(res["time"]*1000)])
        return [{ "target": '1m', "datapoints": _1m},
                { "target": '5m', "datapoints": _5m},
                { "target": '15m', "datapoints": _15m}]

    def data_series_mem_free(self,req):
        """
        空闲内存
        """
        kw = {"time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.Dcol, limit=500, **kw)
        _mem_free = []
        for res in get_series:
            if not res is None: _mem_free.append([res['mem_free'], int(res["time"]*1000)])
        return [{"target": "mem_free", "datapoints": _mem_free}]

    def data_series_netflow(self, req):
        """
        网络流量
        """
        kw = {"time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.Dcol, limit=500, **kw)
        _recv_list=[]
        _send_list=[]
        for res in get_series:
            if not res is None:
                _recv_list.append([float(res['recv']), int(res["time"]*1000)])
                _send_list.append([float(res['send']), int(res["time"]*1000)])
        return [{ "target": 'recv', "datapoints": _recv_list},
                { "target": 'send', "datapoints": _send_list}]

    def data_series_exception_packet(self,req):
        """
        异常数据包
        """
        get_series = CacheServer().find_aggregate(self.Bcol, [{"$group": {"_id": "$time", "total": { "$sum": "$total" }}}])
        _packet = []
        for res in get_series:
            if not res is None:
                _packet.append([res['total'], int(res["_id"]*1000)])
            else:
                _packet.append([0, int(time.time()*1000)])
        return [{ "target": 'excep_packet', "datapoints": _packet}] 

    def data_table_bolt_tcp(self, req):
        """
        TCP数据记录
        """
        kw = { "src": {"$nin": _LISTEN_IP}, "time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.TCPcol, limit=500, **kw)
        _list = []
        for res in get_series:
            _line = [res["proto"], res["src"], res["sport"], res["dst"], res["dport"], res["ttl"], res["flags"], (res["time"]*1000)]
            if not res is None: _list.append(_line)
        return [{
            "columns":[
              {"text":"proto", "type":"string"},
              {"text":"src", "type":"string"},
              {"text":"sport", "type":"string"},
              {"text":"dst", "type":"string"},
              {"text":"dport", "type":"string"},
              {"text":"ttl", "type":"number"},
              {"text":"flags", "type":"string"},
              {"text":"time", "type":"time"}],
            "rows": _list ,
            "type":"table"
            }]

    def data_table_bolt_udp(self, req):
        """
        UDP数据记录
        """
        kw = {"src": {"$nin": _LISTEN_IP}, "time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.UDPcol, limit=500, **kw)
        _list = []
        for res in get_series:
            _line = [res["proto"], res["src"], res["sport"], res["dst"], res["dport"], res["ttl"], (res["time"]*1000)]
            if not res is None: _list.append(_line)
        return [{
            "columns":[
              {"text":"proto", "type":"string"},
              {"text":"src", "type":"string"},
              {"text":"sport", "type":"string"},
              {"text":"dst", "type":"string"},
              {"text":"dport", "type":"string"},
              {"text":"ttl", "type":"number"},
              {"text":"time", "type":"time"}],
            "rows": _list ,
            "type":"table"
            }]

    def data_table_active_table(self, req):
        """
        执行列表
        """
        kw = {"time": {"$gte": convert_time_ms_agg(req['range']['from']), "$lte": convert_time_ms_agg(req['range']['to'])} }
        get_series = CacheServer().find_conditions(self.Bcol, limit=500, **kw)
        _list = []
        for res in get_series:
            if not res is None: _list.append([res["_id"], (res["time"]*1000), res["confname"], res["total"], res["command"]])
        return [{
            "columns":[
              {"text":"_ID", "type":"string"},
              {"text":"Time", "type":"time"},
              {"text":"ConfName", "type":"string"},
              {"text":"Total", "type":"number"},
              {"text":"Command", "type":"string"}],
            "rows": _list ,
            "type":"table"
            }]

