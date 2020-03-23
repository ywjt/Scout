
# Scout web for grafana server

scout_v0.3.0-beta 已集成了用于grafana展示的api接口，你只需要安装 grafana server 再导入json模板即可。

## 安装 grafana server 6.4.4  
* Ubuntu & Debian  
```shell
wget https://dl.grafana.com/oss/release/grafana_6.4.4_amd64.deb
sudo dpkg -i grafana_6.4.4_amd64.deb
````

* Redhat & Centos  
```shell
wget https://dl.grafana.com/oss/release/grafana-6.4.4-1.x86_64.rpm
sudo yum install initscripts urw-fonts
sudo rpm -Uvh grafana-6.4.4-1.x86_64.rpm
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
sudo grafana-cli plugins install simpod-json-datasource
sudo service grafana-server restart
```

* 后台配置 simple-json  
1、添加datasource  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/6F7268C1-9277-4516-B5D7-2D95477EF22C.png'>  

2、选择JSON引擎  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/FD2AF693-B35A-4B67-A07C-6E5B29FC666A.png'>  

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



