
# Scout Plugin for grafana server

这是一个简单的JSON数据源服务器，用于grafana的展示。     
只需要导入模板即可，前提是已安装了grafana server。    

关于grafana SimpleJSON datasource   
可以关注：https://github.com/grafana/simple-json-datasource   
   
  
  
下载直接运行 Scout_grafana_server 即可，建议放到 Scout目录里。

```shell
wget https://github.com/ywjt/Scout/releases/download/v0.1.0-alpha_plugin/Scout_plugin_for_grfana_server.tar.gz
mkdir /usr/local/scout/plugin
tar zxvf Scout_plugin_for_grfana_server.tar.gz -C /usr/local/scout/
ln -s /usr/local/scout/plugin/Scout_plugin /usr/local/bin/

nohup /usr/local/bin/Scout_plugin > /var/log/scout/scout_pulgin.log &
```


## 安装 grafana server 6.4.4  
* Ubuntu & Debian  
```shell
wget https://dl.grafana.com/oss/release/grafana_6.4.4_amd64.deb
sudo dpkg -i grafana_6.4.4_amd64.deb
````

* Redhat & Centos  
```shell
wget https://dl.grafana.com/oss/release/grafana-6.4.4-1.x86_64.rpm
sudo yum localinstall grafana-6.4.4-1.x86_64.rpm
```

* 启动 grafana server
```shell
service grafana-server start
```

* 打开Web界面 http://IP:3000/
```shell
帐号 admin
密码 admin
```

## 导入模板
* 安装 grafana-simple-json-datasource 插件
```shell
sudo grafana-cli plugins install grafana-simple-json-datasource
sudo service grafana-server restart
```

* 后台配置 simple-json  
1、添加datasource  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/6F7268C1-9277-4516-B5D7-2D95477EF22C.png'>  

2、选择JSON引擎  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/7A8FC79A-1133-423B-94DA-3C686A035778.png'>  

3、配置JSON引擎接口  
```shell
这里只需要把URL填入 http://localhost:6667 即可。插件仅允许本地通信，6667端口为固定不可改。
```   
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/EEAF5357-D03F-41F8-B574-CEF4ECC570F2.png'> 

4、导入JSON模板  
```shell
Scout_plugin_for_grafana_server.json
```
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/6563C7A9-A76A-4851-BF53-91D6CF08CE4F.png'> 

5、最终效果  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/web_demo.png'> 



