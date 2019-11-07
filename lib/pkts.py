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

import socket
import dpkt
import binascii
import struct
import uuid
import re
import time
import datetime
import shutil
import os
import sys
import pcapy
from dpkt.compat import compat_ord
from lib.cache import CacheServer
from lib import async, Loger





class Pcapy(object):

    def __init__(self, **kwargs):
        self.interface=kwargs["interface"] if kwargs["interface"] else 'any'
        self.filters=kwargs["filters"]
        self.__max_bytes=kwargs["max_bytes"]
        self.__promiscuous=kwargs["promiscuous"]
        self.__buffer_timeout=kwargs["buffer_timeout"]
        self.__expire_after_seconds=kwargs["expire_after_seconds"]

        """Instant a CacheServer

            exptime:
                expireAfterSeconds: <int> Used to create an expiring (TTL) collection. 
                MongoDB will automatically delete documents from this collection after <int> seconds. 
                The indexed field must be a UTC datetime or the data will not expire.
        """
        self.Cache=CacheServer().create_or_connect_cache()
        self.TCPcol=self.Cache["TCP"]
        self.UDPcol=self.Cache["UDP"]
        CacheServer().create_index(self.TCPcol, "exptime", self.__expire_after_seconds)
        CacheServer().create_index(self.UDPcol, "exptime", self.__expire_after_seconds)

    @async
    def load_cache(self, collection_obj, stdout):
        CacheServer().insert_one(collection_obj, stdout)
        

    def mac_addr(self, address):
        """Convert a MAC address to a readable/printable string

           Args:
               address (str): a MAC address in hex form (e.g. '\x01\x02\x03\x04\x05\x06')
           Returns:
               str: Printable/readable MAC address
        """
        return ':'.join('%02x' % compat_ord(b) for b in address)



    def inet_to_str(self, inet):
        """Convert inet object to a string

            Args:
                inet (inet struct): inet network address
            Returns:
                str: Printable/readable IP address
        """
        # First try ipv4 and then ipv6
        try:
            return socket.inet_ntop(socket.AF_INET, inet)
        except ValueError:
            return socket.inet_ntop(socket.AF_INET6, inet)


    '''
        # 分析以太网头部信息
        数据包包含 Ethernet->TCP/UDP/ICMP/ARP->RAW三个层次
        第一层是网络层，包含源、目的mac、ip协议号
        第二层是协议层，包含源ip、目标ip（除arp、icmp）
        第三层是元数据，包含端口号、http报文
    '''
    def ether(self, hdr, buf):
        try:
            # Unpack the Ethernet frame (mac src/dst, ethertype)
            eth = dpkt.ethernet.Ethernet(buf)

            # Make sure the Ethernet data contains an IP packet
            if not isinstance(eth.data, dpkt.ip.IP):
                Loger().CRITICAL('IP Packet type not supported %s' % eth.data._class_._name_)
                raise

            # 让以太网帧的ip数据报部分等于一个新的对象，packet
            packet=eth.data
            stdout={}
            #stdout["time"]=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            stdout["time"]=int(time.time())
            stdout["exptime"]=datetime.datetime.utcnow()
            stdout["mac_src"]=self.mac_addr(eth.src)
            stdout["mac_dst"]=self.mac_addr(eth.dst)
            stdout["eth_type"]=eth.type
            stdout["length"]=packet.len
            stdout["ttl"]=packet.ttl

            """protocol number
                packet.p:
                    1 : ICMP Packets
                    6 : TCP protocol
                    8 : IP protocol
                   17 : UDP protocol
            """
            if packet.p==6:
                self.recv_tcp(packet, stdout)
            elif packet.p==17:
                self.recv_udp(packet, stdout)
            else:
                Loger().WARNING('Protocol type not supported %s' % eth.data._class_._name_)
                pass

        except Exception as e:
            raise


    def recv_http(self, ip):
        # 确保对象在传输层
        if isinstance(ip.data, dpkt.tcp.TCP):
            '''
                # 解析出http请求数据
                  包含一个元组数据，比如
                    Request(body='', uri=u'/okokoko', headers=OrderedDict([(u'host', u'1.1.1.1'), 
                                (u'user-agent', u'curl/7.54.0'), (u'accept', u'*/*')]), version=u'1.1', data='', method=u'GET')
            '''
            tcp = ip.data
            try:
                request=dpkt.http.Request(tcp.data)
                req_dict={}
                req_dict["url"]=request.uri
                req_dict["method"]=request.method
                req_dict["version"]=request.version
                req_dict["headers"]={
                                "host": request.headers["host"],
                                "user-agent": request.headers["user-agent"],
                                        }
                return req_dict
            except (dpkt.dpkt.NeedData, dpkt.dpkt.UnpackError):
                #Loger().WARNING('Http data Unpack Error: %s' % dpkt.dpkt.UnpackError)
                pass
            


    def recv_tcp(self, packet, stdout):
        if True:
            try:
                tcp=packet.data
                stdout["proto"]='TCP'

                '''
                    日常的分析有用的五个字段：
                    FIN表示关闭连接
                    SYN表示建立连接
                    RST表示连接重置
                    ACK表示响应
                    PSH表示有DATA数据传输

                    其中，ACK是可能与SYN，FIN等同时使用的，比如SYN和ACK可能同时为1，它表示的就是建立连接之后的响应，如果只是单个的一个SYN，它表示的只是建立连接。
                    TCP的几次握手就是通过这样的ACK表现出来的。但SYN与FIN是不会同时为1的，因为前者表示的是建立连接，而后者表示的是断开连接。
                    RST一般是在FIN之后才会出现为1的情况，表示的是连接重置。一般地，当出现FIN包或RST包时，我们便认为客户端与服务器端断开了连接；
                    而当出现SYN和SYN＋ACK包时，我们认为客户端与服务器建立了一个连接。
                    PSH为1的情况，一般只出现在 DATA内容不为0的包中，也就是说PSH为1表示的是有真正的TCP数据包内容被传递。
                    TCP的连接建立和连接关闭，都是通过请求－响应的模式完成的。

                    三次握手确认建立一个连接：
                    位码即tcp标志位，有6种标示：
                    SYN(synchronous建立联机)
                    ACK(acknowledgement 确认)
                    PSH(push传送)
                    FIN(finish结束)
                    RST(reset重置)
                    URG(urgent紧急)
                    Sequence number(顺序号码)
                    Acknowledge number(确认号码)
                    第一次握手：主机A发送位码为syn＝1，随机产生seq number=1234567的数据包到服务器，主机B由SYN=1知道，A要求建立联机；
                    第二次握手：主机B收到请求后要确认联机信息，向A发送ack number=(主机A的seq+1)，syn=1，ack=1，随机产生seq=7654321的包；
                    第三次握手：主机A收到后检查ack number是否正确，即第一次发送的seq number+1，以及位码ack是否为1，若正确，主机A会再发送ack number=(主机B的seq+1)，ack=1，主机B收到后确认seq值与ack=1则连接建立成功。
                    完成三次握手，主机A与主机B开始传送数据。
                '''
                if   tcp.flags&dpkt.tcp.TH_FIN:  flags='fin'
                elif tcp.flags&dpkt.tcp.TH_SYN:  flags='syn'
                elif tcp.flags&dpkt.tcp.TH_RST:  flags='rst'
                elif tcp.flags&dpkt.tcp.TH_PUSH: flags='psh'
                elif tcp.flags&dpkt.tcp.TH_ACK:  flags='ack'
                elif tcp.flags&dpkt.tcp.TH_URG:  flags='urg'
                elif tcp.flags&dpkt.tcp.TH_ECE:  flags='ece'
                elif tcp.flags&dpkt.tcp.TH_CWR:  flags='cwr'
                else: flags='.'

                stdout["src"]=self.inet_to_str(packet.src)
                stdout["dst"]=self.inet_to_str(packet.dst)
                stdout["sport"]=tcp.sport
                stdout["dport"]=tcp.dport
                stdout["flags"]=flags
                stdout["seq"]=tcp.seq
                stdout["ack"]=tcp.ack
                stdout["sum"]=tcp.sum

            except Exception as e:
                pass

            #尝试解出http的数据包
            stdout["RAW"]=self.recv_http(packet)
            #写入缓存
            self.load_cache(self.TCPcol, stdout)
            #Loger().INFO(stdout)


    def recv_udp(self, packet, stdout):
        if True:
            try:
                udp=packet.data
                stdout["proto"]='UDP'
                stdout["src"]=self.inet_to_str(packet.src)
                stdout["dst"]=self.inet_to_str(packet.dst)
                stdout["sport"]=udp.sport
                stdout["dport"]=udp.dport
                stdout["sum"]=udp.sum
                stdout["RAW"]={}

                if udp.dport==53:
                    dns = dpkt.dns.DNS(udp.data)
                    try:
                        r_ip = socket.inet_ntoa(dns.an[1].ip)  # dns返回ip
                    except:
                        r_ip = ""  # dns请求，则没有ip返回
                    stdout["RAW"]={'id':dns.id, 'qd':dns.qd[0].name, 'ip':r_ip}

            except Exception as e:
                pass

            #写入缓存
            self.load_cache(self.UDPcol, stdout)
            #Loger().INFO(stdout)
            

    '''
    def recv_icmp(self, packet):
        if True:
            try:
                icmp=packet.data
                if isinstance(icmp, dpkt.icmp.ICMP):
                    stdout["src"]=self.inet_to_str(packet.src)
                    stdout["dst"]=self.inet_to_str(packet.dst)
                    stdout["type"]=icmp.type
                    stdout["code"]=icmp.code
                    stdout["sum"]=icmp.sum
                    stdout["RAW"]=icmp.data
            except Exception as e:
                print e
                raise
            print stdout
    '''

    def data_link_str(self, link_type):
        if link_type==1:
            return 'Ethernet (10Mb, 100Mb, 1000Mb, and up); the 10MB in the DLT_ name is historical.'
        elif link_type==6:
            return 'IEEE 802.5 Token Ring; the IEEE802, without _5, in the DLT_ name is historical.'
        elif link_type==105:
            return 'IEEE 802.11 wireless LAN.'
        else:
            return 'unknow link type.'

    '''
        max_bytes
        捕获数据包的最大字节数

        promiscuous
        混杂模式就是接收所有经过网卡的数据包，包括不是发给本机的包，即不验证MAC地址
        普通模式下网卡只接收发给本机的包（包括广播包）传递给上层程序，其它的包一律丢弃

        read_timeout
        每次捕获的时间间隔，单位milliseconds

        packet_limit
        捕获的次数，小于或等于0时 表示不限制
    '''
    def DUMP(self):
        pcapy.findalldevs()
        p = pcapy.open_live(self.interface, self.__max_bytes, self.__promiscuous, self.__buffer_timeout)
        p.setfilter(self.filters)
        packet_limit= -1
        print("Listen: %s, net=%s, mask=%s, linktype=[%d, %s] \n\n" % (self.interface, p.getnet(), p.getmask(), p.datalink(), self.data_link_str(p.datalink())))
        p.loop(packet_limit, self.ether)






