# Scout v0.1.0-alpha

Scout是一个攻击检测工具，它在受到如CC、压测工具、syn flood、udp flood等拒绝服务攻击时，能进实时检测和告警。同时支持配置防火墙的封锁，也可以通过调用脚本做一些其它的处理。本工具实际上在原来Dshield工具上重构而来的，但实现的方式与原来完全不一样。本次方案是以调用libcap数据包捕获的开源函数库来收集，经过适配器的所有数据，然后将数据进行实时分析。

本具集成了一个用于缓存数据的软件（目前是mongodb），你不用额外去安装它，工具里已经打包集成了，直接通过工具命令来启动就行。 

按照原来的架构规划，Scout是一个分布式的预警平台，由于时间精力原因，目前只做了一个单机试用版本。 后面有精力会重写成分布架构，独立开发一个中央管理后台，来管理所有在主机上跑的Scout客户端。可以通过中央后台分发策略文件，支持线上配置、线上查询分析数据、控制Scout客户端、集中告警等。

## 架构原理
<img src='https://github.com/ywjt/Scout/blob/master/Scout_ObServer.png'> 

**PS：目前仅实现Scout客户端部份。**   


## 运行环境：
* 支持 Centos6、Centos7
* 支持 Ubuntu14.04、Ubuntu16.04 (新增)
* 添加 grafana 展示插件 (新增)
* 使用root特权运行
* 注意下载对应的版本 

<img src='https://github.com/ywjt/Scout/blob/master/plugin/web_demo.png'>

## 配置文件有两种：  
* 全局启动配置 scoutd.conf  
* 预警策略配置（支持yaml、json格式），语法不能有错，暂时没有做过多的语法校验。已内置了3个策略模板。   
* 路径：/etc/scout.d/


## 安装Scout
**PS：由于github上传最大限制25M，在上面bin目录中缺少cacheServer可执行文件，直接clone上面代码没法运行。**

1）解压到指定目录  
* Centos6\7:  
```shell
wget https://github.com/ywjt/Scout/releases/download/v0.1.0-alpha/Scout_v0.1.0-alpha.tar.gz  
tar zxvf Scout_v0.1.0-alpha.tar.gz -C /usr/local/  
```

* Ubuntu14.04\16.04:  
```shell
https://github.com/ywjt/Scout/releases/download/v0.1.0-alpha_ubuntu/Scout_v0.1.0-alpha_ubuntu.tar.gz   
tar zxvf Scout_v0.1.0-alpha_ubuntu.tar.gz -C /usr/local/  
```

2）设置软连接
```shell
ln -s /usr/local/scout/conf /etc/scout.d  
ln -s /usr/local/scout/bin/* /usr/local/bin/  
```

如果是 Centos7:
```shell
ln -s /usr/lib64/libsasl2.so.3.0.0 /usr/lib64/libsasl2.so.2  
```

3）初始化缓存目录   
```shell
Scoutd init  
```

这一步在新安装时要做，还有如果全局配置文件里改变了storage_type缓存类型，也需要重新初始化。重新初始化会清除缓存数据。  
修改/etc/scout.d/scoutd.conf 的 listen_ip ="",然后可以启动了。

4）启动Scout  
```shell
Scoutd start  
Scoutd version  
```
**PS：确保你的系统已安装iptables 防火墙，本具默认使用iptables，否则无法实现封禁操作。当然你也可以在策略文件中关闭它。如果是Ubuntu请额外安装支持iptables，然后把UFW关闭。**


5）可以查看运行状态  
```shell
Scoutd status  
Scoutd dstat 
```

6）可以监听日志输出  
```shell
Scoutd watch  
```

7）其它使用帮助  
```shell
Scoutd help  
```

```shell
Usage: Scoutd 
                          
 Options:  
        init       creating and initializing a new cache partition. 
        start      start all service. 
        stop       stop main proccess, cacheserver keep running. 
        restart    restart main proccess, cacheserver keep running. 
        reload     same as restart. 
        forcestop  stop all service, include cacheserver and main proccess. 
        reservice  restart cacheserver and main proccess. 
        status     show main proccess run infomation. 
        dstat      show generating system resource statistics. 
        view       check block/unblock infomation. 
        watch      same as tailf, watching log output. 
        help       show this usage information. 
        version    show version information. 
```


## 全局配置说明
```shell
#日志输出等级,选项：DEBUG，INFO，WARNING，ERROR，CRITICAL
log_level = "INFO"

#本机监听,填写本机所有通信IP,不要填0.0.0.0
listen_ip = "10.10.0.4,114.114.114.114"

# 信任IP列表,支持CIRD格式
trust_ip = "10.10.10.0/24,172.16.0.0/16"

# 监听适配器,如果是多网口,请填写'any'，否则填'eth0|eth1|em0|em1...'
motr_interface = "eth0"

# 监听端口,可以多个 如: "443,80,8080"
motr_port = "80,443,53"

# 捕获数据包的最大字节数, 相当于buffer_timeout时间内的缓冲区
max_bytes = 65536

# 定义适配器是否必须进入混杂模式
# 关于混杂模式,如果启用则会把任何流过网口的数据都会捕获，这样会产生很多杂乱的数据
# 要精准捕获由外网流入的数据, 建议设为 False
promiscuous = False

# 缓冲区超时时间,单位是毫秒,一般设1000ms即可
# 当捕获程序在设定的超时周期内返回一次数据集
buffer_timeout = 1000

# 自动删除缓存记录的存活时间,单位秒
# 默认: 86400 (1 days)
expire_after_seconds = 86400

# 缓存数据的方式，可选：'Memory' 或 'Disk'
# Memory 内存方式，若服务关闭数据会被重置，检测效率高，准确性高
# Disk 磁盘方式，数据会被持久化，检测效率低，需要通过提高策略阀值达到预警
# 不支持动态切换，如果首次启动后，切换缓存方式，需要重新初始化缓存服务，执行 Scoutd init
storage_type = 'Memory'

# 限制内存使用大小，最小1G
# 不配置默认为可用系统内存的一半，配置不能有小数点
storage_size = 1
```


## 策略配置说明

**Bolt Fields**  
<table>
    <tr><td>Field</td><td>Desc</td><td>Bolt</td></tr>
    <tr><td>mac_src</td><td>来源MAC</td><td>TCP,UDP</td></tr>
    <tr><td>mac_dst</td><td>目标MAC</td><td>TCP,UDP</td></tr>
    <tr><td>src</td><td>来源IP</td><td>TCP,UDP</td></tr>
    <tr><td>dst</td><td>目标IP</td><td>TCP,UDP</td></tr>
    <tr><td>sport</td><td>来源Port</td><td>TCP,UDP</td></tr>
    <tr><td>dport</td><td>目标Port</td><td>TCP,UDP</td></tr>
    <tr><td>proto</td><td>访问协议</td><td>TCP,UDP</td></tr>
    <tr><td>ttl</td><td>来源ttl值</td><td>TCP,UDP</td></tr>
    <tr><td>flags</td><td>连接状态</td><td>TCP</td></tr>
    <tr><td>time</td><td>记录时间戳</td><td>TCP,UDP</td></tr>
<table>

上述列出的Field可以用于策略文件的编写，要怎么实现查询想要的数据，就需要自行构造了。策略文件的filter模块始终都是以类似SQL的聚合查询语法来执行。

```shell
SELECT count({Field}) AS total , {Field}
FROM TCP
WHERE (time >= 1573110114 AND time <= 1573110144)
AND ...
GROUP BY {Field}
HAVING count({Field}) > 100
```

**策略文件例子**
```yaml
name: "CC attack check"  #策略名称
desc: ""  #简单描述一下
ctime: "Thu Oct 24 17:48:11 CST 2019"  #创建时间

# 缓存表,目前只有TCP、UDP两个表,实际上是指定分析的数据源
bolt: "TCP"

# 过滤器,类似于SQL查询
# ```
#   SELECT count(src) AS total , src
#   FROM TCP
#   WHERE dport IN (80, 443)
#     AND (time >= 1573110114 AND time <= 1573110144)
#     AND src NOT IN ('127.0.0.1', '10.10.0.4', '114.114.114.114')
#   GROUP BY src
#   HAVING count(src) > 100
# ```
# 返回：{u'total': 121, u'_id': u'115.115.115.115'}
#
filter:
    timeDelta: 30           #时间区间, Seconds.
    trustIps:               #排除src白名单,列表
      - 127.0.0.1
      - 10.10.0.4
      - 114.114.114.114
    motrPort:               #过滤端口,列表
      - 80
      - 443
    motrProto: "TCP"        #过滤协议,TCP或UDP(暂时没有区分更细的协议名，如http、https、ssh、ftp、dns等)
    flags: ""               #TCP握手的状态 (常见syn、ack、psh、fin)
    noOfConnections: 100    #聚合的阀值,结合noOfCondition|returnFiled，如group by src having count(src) $gte 1000
    noOfCondition: "$gte"   #聚合阀值条件, 如$ge\$gt\$gte\$lt\$lte
    returnFiled: "src"      #聚合的字段名, blot表里必须存在

# 执行模块
block:
    action: true     #是否封禁
    expire: 300      #封禁时间，Seconds.
    iptables: true   #默认是用防火墙封禁,如果自定义脚本,这里设为false，如果为true，blkcmd/ubkcmd则为空，否则填了也不会生效
    blkcmd: ""       #锁定时执行，传参为 returnFiled 列表值（你可以用脚本来扩展，注意执行权限）
    ubkcmd: ""       #解锁时执行，传参为 returnFiled 列表值（你可以用脚本来扩展，注意执行权限）

# 通知模块
notice:
    send: true       #是否发送
    email:    
      - 350311204@qq.com   #接收人邮箱，列表
      
```
   
   
## 安装grafana插件（可选）  
参考文档： https://github.com/ywjt/Scout/tree/master/plugin   
   
   
## 模拟测试
下面使用hping3 工具发起攻击测试，工具自行安装。hping3是一个很全面的网络压测工具。  

**发起80端口syn半连接请求**
```shell
hping3 -I eth0 -S 目标IP -p 80 --faster
```

**发起53端口udp flood**
```shell
hping3 -2 -I eth0 -S 目标IP -p 53 --faster
```

**监听Scout输出**
```shell
[root@host-10-10-0-4 ~]# Scoutd watch
logging output ......
2019-11-07 16:11:27 __init__.py[line:1601] WARNING [LOCK] syn has been blocked, It has 606 packets transmitted to server.
2019-11-07 16:11:28 __init__.py[line:1585] ERROR [MAIL] Send mail failed to: [Errno -2] Name or service not known
2019-11-07 16:11:29 __init__.py[line:1601] WARNING [syn.yaml] {u'total': 606, u'_id': u'syn', 'block': 1}
2019-11-07 16:11:30 __init__.py[line:1601] WARNING [LOCK] 117.*.*.22 has been blocked, It has 861 packets transmitted to server.
2019-11-07 16:11:32 __init__.py[line:1585] ERROR [MAIL] Send mail failed to: [Errno -2] Name or service not known
2019-11-07 16:11:32 __init__.py[line:1601] WARNING [tcp.yaml] {u'total': 861, u'_id': u'117.*.*.22'}
2019-11-07 16:11:36 __init__.py[line:1601] WARNING [LOCK] 117.*.*.25 has been blocked, It has 904 packets transmitted to server.
2019-11-07 16:11:38 __init__.py[line:1585] ERROR [MAIL] Send mail failed to: [Errno -2] Name or service not known
2019-11-07 16:11:39 __init__.py[line:1601] WARNING [udp.yaml] {u'total': 904, u'_id': u'117.*.*.25'}
2019-11-07 16:11:39 __init__.py[line:1601] WARNING [syn.yaml] {u'total': 1765, u'_id': u'syn', 'block': 1}
2019-11-07 16:11:40 __init__.py[line:1601] WARNING [tcp.yaml] {u'total': 1817, u'_id': u'117.*.*.22'}
2019-11-07 16:11:43 __init__.py[line:1601] WARNING [udp.yaml] {u'total': 1806, u'_id': u'117.*.*.25'}
```

可以发现所有策略文件都被执行了，并达到预警阀值。再查看封锁记录。

```shell
[root@host-10-10-0-4 ~]# Scoutd view
+------------+----------+-------+------------------------------------------------------------+---------------------+
|    _ID     | ConfName | Total |                          Command                           |         Time        |
+------------+----------+-------+------------------------------------------------------------+---------------------+
|      syn   |   syn    |  371  | /opt/notice.sh {u'total': 371, u'_id': u'syn', 'block': 1} | 2019-11-07 16:12:06 |
| 117.*.*.22 |   tcp    |  371  |      /sbin/iptables -I INPUT -s 117.*.*.22 -j DROP         | 2019-11-07 16:12:06 |
| 117.*.*.25 |   udp    |  604  |      /sbin/iptables -I INPUT -s 117.*.*.25 -j DROP         | 2019-11-07 16:12:09 |
+------------+----------+-------+------------------------------------------------------------+---------------------+
```

目前Scout的性能还不算很高，如果有大量持续的攻击，CPU占用率稍有些高的，一旦攻击停止占用率就会马上降下来。

```shell
[root@host-10-10-0-4 ~]# Scoutd dstat 
+---------------------+------+------+-------+------+--------------+-----------+-----------+
|         Time        | 1min | 5min | 15min | %CPU | MemFree(MiB) | Recv(MiB) | Send(MiB) |
+---------------------+------+------+-------+------+--------------+-----------+-----------+
| 2019-11-07 16:29:33 | 0.00 | 0.04 |  0.05 | 0.5  |     4307     |   0.002   |   0.002   |
| 2019-11-07 16:30:36 | 0.00 | 0.03 |  0.05 | 0.5  |     4258     |   0.000   |   0.000   |
| 2019-11-07 16:31:40 | 0.77 | 0.21 |  0.11 | 43.9 |     4291     |   3.754   |   0.001   |
| 2019-11-07 16:32:43 | 0.67 | 0.33 |  0.16 | 0.2  |     4300     |   0.000   |   0.000   |
+---------------------+------+------+-------+------+--------------+-----------+-----------+
```


## About

**Original Author:** YWJT http://www.ywjt.org/ (Copyright (C) 2016)  
**Maintainer:** ZhiQiang Koo <350311204@qq.com>  
<img src="http://www.ywjt.org/ywjtshare.png" width="200px">  


