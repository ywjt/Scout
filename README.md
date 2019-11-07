# Scout

Scout是一个攻击检测预警工具，它在受到如CC、压测工具、syn flood、udp flood等拒绝服务攻击时，能进实时检测和告警。同时支持配置防火墙的封锁，也可以通过调用脚本做一些其它的处理。本工具实际上在原来Dshield工具上重构而来的，但实现的方式与原来完全不一样。本次方案是以调用libcap数据包捕获的开源函数库来收集，经过适配器的所有数据，然后将数据进行实时分析。

本具集成了一个用于缓存数据的软件（目前是mongodb），你不用额外去安装它，工具里已经打包集成了，直接通过工具命令来启动就行。 本工具没有Dshield的高大上图形界面了，但实际上还是可以通过Grafana来展示，后面再补一个插件。

按照原来的架构规划，Scout是一个分布式的预警平台，由于时间精力原因，目前只做了一个单机试用版本。 后面有精力会重写成分布架构，独立开发一个中央管理后台，来管理所有在主机上跑的Scout客户端。可以通过中央后台分发策略文件，支持线上配置、线上查询分析数据、控制Scout客户端、集中告警等。


运行环境：
* 仅支持 Centos6、Centos7。
* python 2.7

配置文件有两种：
1）全局启动配置 scoutd.conf
2）预警策略配置（支持yaml、json格式），语法不能有错，暂时没有做过多的语法校验。已内置了3个策略模板。


【安装Scout】

1）解压到指定目录
wget https://github.com/ywjt/Scout/releases/download/v0.1.0-alpha/Scout_v0.1.0-alpha.tar.gz
tar zxvf Scout_v0.1.0-alpha.tar.gz -C /usr/local/

2）设置软连接
n -s /usr/local/scout/conf /etc/scout.d
ln -s /usr/local/scout/bin/* /usr/local/bin/

如果是 Centos7:
ln -s /usr/lib64/libsasl2.so.3.0.0 /usr/lib64/libsasl2.so.2

3）初始化缓存目录
Scoutd init

这一步在新安装时要做，还有如果全局配置文件里改变了storage_type缓存类型，也需要重新初始化。重新初始化会清除缓存数据。

4）启动Scout
Scoutd start
Scoutd version

5）可以查看运行状态
Scoutd status
Scoutd dstat

6）可以监听日志输出
Scoutd watch

7）其它使用帮助
Scoutd help

"""
Usage: Scoutd

Options:
[init] -- creating and initializing a new cache partition.
[start] -- start all service.
[stop] -- stop main proccess, cacheserver keep running.
[restart] -- restart main proccess, cacheserver keep running.
[reload] -- same as restart.
[forcestop] -- stop all service, include cacheserver and main proccess.
[reservice] -- restart cacheserver and main proccess.
[status] -- show main proccess run infomation.
[dstat] -- show generating system resource statistics.
[view] -- check block/unblock infomation.
[watch] -- same as tailf, watching log output.
[help] -- show this usage information.
[version] -- show version information.
"""


【全局配置说明】


【策略配置说明】

