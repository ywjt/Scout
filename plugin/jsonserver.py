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
import sys, os
sys.path.append("..")
import _strptime
import logging
from calendar import timegm
from datetime import datetime
from images import CacheServer, GetSeries
from flask import Flask, request, jsonify
from base import ScoutBase
from base import CONF_DIR, LOGS_DIR

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)
app = Flask("Scout plugin for grafana server")


#return '/search' KEYS
__SCOUT_KEYS= ['cpu_percent', 'loadavg', 'mem_free', 'netflow', 'uptime', 'bolt_tcp', 'bolt_udp', 'active_table', 'excep_packet']


def get_main_pid():
    try:
        f = open(LOGS_DIR + "scoutd.pid", 'r')
        PID = f.read()
        f.close()
        return PID
    except IOError as e:
        return 0


def convert_to_time_ms(timestamp):
    return 1000 * timegm(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple())


@app.route('/')
def health_check():
    return 'This datasource is healthy.'


@app.route('/search', methods=['POST'])
def search():
    return jsonify(__SCOUT_KEYS)


@app.route('/query', methods=['POST'])
def query():
    req = request.get_json()
    for item in req['targets']:
        if item['target'] == 'uptime':
            data = GetSeries().data_series_uptime(req, int(get_main_pid()))
        elif item['target'] == 'netflow':
            data = GetSeries().data_series_netflow(req)
        elif item['target'] == 'cpu_percent':
            data = GetSeries().data_series_cpu_percent(req)
        elif item['target']== 'mem_free':
            data = GetSeries().data_series_mem_free(req)
        elif item['target'] == 'loadavg':
            data = GetSeries().data_series_load_average(req)
        elif item['target'] == 'excep_packet':
            data = GetSeries().data_series_exception_packet(req)
        elif item['target'] in ['active_table']:
            data = GetSeries().data_table_active_table(req)
        elif item['target'] in ['bolt_tcp']:
            data = GetSeries().data_table_bolt_tcp(req)
        elif item['target'] in ['bolt_udp']:
            data = GetSeries().data_table_bolt_udp(req)
        else:
            data = []
    return jsonify(data)


@app.route('/annotations', methods=['POST'])
def annotations():
    req = request.get_json()
    data = [
        {
            "annotation": 'This is the annotation',
            "time": (convert_to_time_ms(req['range']['from']) +
                     convert_to_time_ms(req['range']['to'])) / 2,
            "title": 'Deployment notes',
            "tags": ['tag1', 'tag2'],
            "text": 'Hm, something went wrong...'
        }
    ]
    return jsonify(data)


@app.route('/tag-keys', methods=['POST'])
def tag_keys():
    data = [
        {"type": "string", "text": "TCP"},
        {"type": "string", "text": "DSTAT"}
    ]
    return jsonify(data)


@app.route('/tag-values', methods=['POST'])
def tag_values():
    req = request.get_json()
    if req['key'] == 'TCP':
        return jsonify([
            {'text': 'syn'},
            {'text': 'ack'},
            {'text': 'fin'}
        ])
    elif req['key'] == 'DSTAT':
        return jsonify([
            {'text': '1m'},
            {'text': '5m'},
            {'text': '15m'},
            {'text': 'mem_free'},
            {'text': 'cpu_percent'},
            {'text': 'recv'},
            {'text': 'send'}
        ])
    


def app_run():
    __HTTP_HOST = ScoutBase().avr['http_host']
    __HTTP_PORT = ScoutBase().avr['http_port']
    app.run(host=__HTTP_HOST, port=__HTTP_PORT, debug=False)
