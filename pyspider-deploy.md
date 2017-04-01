#部署pyspider
## 安装
1.根据官方文档，先执行：
`sudo apt-get install python python-dev python-distribute python-pip libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml`

2.安装pyspider，建议在virtualenv中安装
```bash
 pyenv virtualenv 3.4.0 pyspider
 pyenv activate pyspider 
 pip install pyspider supervisor mysql-connector-python-rf redis pymysql
```

3.安装redis来存储消息队列
`apt-get install redis-server redis-tools`

4.设置配置文件(config.json):
```
{
  "taskdb": "mysql+taskdb://root:password@ip:port/taskdb",
  "projectdb": "mysql+projectdb://root:password@ip:port/projectdb",
  "resultdb": "mysql+resultdb://root:password@ip:port/resultdb",
  "message_queue": "redis://127.0.0.1:6379/1",
  "webui": {
    "username": "any",
    "password": "any",
    "need-auth": true,
    "port": 5001
  }
}
```
5.配置supervisor
```
[program:pyspider]
command=/root/.pyenv/versions/pyspider/bin/pyspider -c config.json
directory=/root/pyspider-clawswjtu
autostart=true
startsecs=0
stopwaitsecs=0
autorestart=true
stdout_logfile=/root/pyspider-clawswjtu/log/pyspider.log
stderr_logfile=/root/pyspider-clawswjtu/log/pyspider.err
```

6.配置防火墙
打开5001端口外部访问:
`iptables -A INPUT -p tcp --dport 5001 -j ACCEPT`

打开http://ip:5001就可以访问pyspider了