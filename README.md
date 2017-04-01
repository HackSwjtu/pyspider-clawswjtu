# pyspider-clawswjtu
查询交大最新讲座信息和学术竞赛信息的微信小程序的爬虫端

目前讲座信息收录的爬取页面为：
1. http://www.swjtu.edu.cn/jsp/activity.jsp?page=1&siteId=12163&catalogPath=-12163-12259-&selectDay=&searchType=month&address=&keyword=&hdType=
2. http://dean.swjtu.edu.cn/servlet/LectureAction?Action=LectureMore&SelectType=Month

竞赛信息收录的爬取页面为：
- TODO

    如果你有其他的稳定的在线讲座或竞赛信息来源，欢迎提issue, 或者发我邮件jonathan.swjtu@gmail.com

爬虫服务端部署见[pyspider-deploy](pyspider-deploy.md)

## 页面爬取规范
### 讲座类

讲座类页面爬取的元素分为：
- 讲座标题(title)
- 讲座类型(lecturetype)
- 讲座时间(lecturetime)
- 讲座地点(place)
- 演讲者(speaker)
- 演讲者简介(speakerbrif)
- 讲座详细内容(detail)

页面内容爬取下来后需要进行相关处理后放入数据库，要求：
1. 所有的元素前面不得加前缀：比如【创源大讲堂】,讲座嘉宾: , 讲座时间:，讲座地点等
2. 讲座时间保存的格式应该为%Y-%m-%d %H:%M
3. 讲座详细内容爬取后需要将html内容转换为markdown格式，然后存储，同时去除多余的标签内容和之前元素重复的内容，比如`© 2012 西南交通大学教务处`
4. 如果一个讲座在多个网页都有，保存的时候需要根据讲座标题去重
5. 讲座类型主要设定为：创源大讲堂，创新讲座，青年讲坛，竞赛相关，普通讲座(后期可根据情况添加)