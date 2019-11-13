
# Scout Plugin for grafana server

这是一个简单的JSON数据源服务器，用于grafana的展示。     
只需要导入模板即可，前提是已安装了grafana server。    

关于grafana SimpleJSON datasource   
可以关注：https://github.com/grafana/simple-json-datasource   
   
  
  
下载直接运行 Scout_grafana_server 即可，建议放到 Scout目录里。

```shell
mkdir /usr/local/scout/plugin
cp Scout_grafana_server /usr/local/scout/plugin/
ln -s /usr/local/scout/plugin/Scout_grafana_server /usr/local/bin/

/usr/local/bin/Scout_grafana_server &
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
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/20AEAE30-A1D0-4D24-9162-736EC6DB76ED.png'>  

3、配置JSON引擎接口  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/7048349F-3AE4-474E-A0F7-069699661B48.png'> 

4、导入JSON模板  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/doc/6563C7A9-A76A-4851-BF53-91D6CF08CE4F.png'> 

5、最终效果  
<img src='https://github.com/ywjt/Scout/blob/master/plugin/web_demo.png'> 



