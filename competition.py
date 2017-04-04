#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Created on 2017-03-28 22:14:07
# Project: LecturePush

from pyspider.libs.base_handler import *
import re
import datetime as dt
from datetime import datetime,timedelta

from pyspider.libs.base_handler import *
import pymysql
from lxml import etree
from tidylib import tidy_document
import urllib2, cookielib, re, jieba

conn = pymysql.connect(host='ip', user='root', passwd='pass', db='db', charset="utf8")
cursor = conn.cursor()

limdate = dt.datetime.now() + dt.timedelta(days=-60) # 日期下限

competition_list = [
    '全国大学生ACM程序设计大赛',
    '全国大学生广告艺术大赛',
    '全国大学生智能车竞赛',
    '全国大学生交通科技竞赛',
    '全国大学生物流设计大赛',
    '全国大学生电子设计竞赛',
    '全国大学生周培源力学竞赛',
    '全国大学生工程训练综合能力竞赛',
    '全国大学生机器人大赛',
    '全国大学生数学建模竞赛',
    '中国大学生互联网创新创业大赛',
    '全国大学生机械创新设计大赛',
    '全国大学生节能减排社会实践与科技竞赛',
    '全国大学生结构设计竞赛',
    '大学生生命之星科技邀请赛',
    '全国大学生物理实验竞赛大学生物理学术竞赛',
    '大学生英语系列挑战赛',
    '创青春大学生课外学术科技作品竞赛与创业计划大赛',
    '中国大学生服务外包创新创业大赛'
]
competition_split = []



class Handler(BaseHandler):
    
    def __init__(self):
        self.conn = conn
        self.cursor = cursor
        sql = '''
            CREATE TABLE IF NOT EXISTS Competition(
              id INT PRIMARY KEY AUTO_INCREMENT,
              title VARCHAR(100),
              publishdate datetime,
              detail TEXT
        )ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;'''
        self.cursor.execute(sql)
        self.conn.commit()
        
        for match in competition_list:
            splitword = jieba.lcut_for_search(match) #中文分词
            onesplit = []
            for word in splitword:
                if re.match('全国|大学|学生|大学生|学院|竞赛|大赛|与|挑战|作品|计划'.decode('utf8'), word) == None:
                    onesplit.append(word)
            competition_split.append(onesplit)
        
    crawl_config = {
        'headers': {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', }
    }



    @every(minutes=3 * 60)
    def on_start(self):
        self.crawl('http://dean.swjtu.edu.cn/servlet/NewsAction?Action=NewsMore',  callback=self.index_page, validate_cert=False, auto_recrawl=True, last_modified=False)


    '''
    工具方法－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－
    '''

    #删除不必要的字符
    def deletetabnenter(self, string):
        # print 'deletetabnenter\t'
        newstring = ''
        for char in string:
            if re.match('[ \n\t“”"、+（）()]'.decode('utf8'), char) == None and char != u'\xa0':
                newstring += char
        return newstring



    def close_crawl(self):
        pass

    def iscompetition(self, title):
        flag = 0
        for cursor in range(len(competition_split)):
            num = 0
            for word in competition_split[cursor]:
                if title.find(word) != -1:
                    num += 1
            if num > 1:
                flag = 1
                break
        if flag == 1:
            return True
        else:
            return False

    '''
    页面处理方法
    '''
    def index_page(self, response):
        newslist = response.doc('ul.IndexMenu li').items()
        for new in newslist:
            if new.text() != "":
                title = self.deletetabnenter(new("div a").text())
                date = new('[style="float:left;width:75px; text-align:center; overflow:hidden;"]').text()
                url = new("div a").attr.href
                publishdate = datetime.strptime(date, '%Y-%m-%d')
                if publishdate < limdate:
                    break
                if re.search('奖|绩|获|记|名单|课|结果|简报|中学生'.decode('utf8'), title) == None and title.find('赛'.decode('utf8')) != -1:
                    if self.iscompetition(title):
                        self.crawl(url, callback=self.dean_competition_detail_page, save={'publishdate': publishdate},last_modified=False)

        pagejs = response.doc('script')
        all_pages = re.findall('var allPage = "(.*?)"', pagejs.text(), re.S)[0]
        current_pages = re.findall('var page = "(.*?)"', pagejs.text(), re.S)[0]
        if int(all_pages) > 1:            
            for page in range(2, int(all_pages) + 1):
                page_link = 'http://dean.swjtu.edu.cn/servlet/NewsAction?Action=NewsMore&page={}'.format(
                    page)
                if page < 5:
                    self.crawl(page_link, callback=self.index_page, last_modified=False)

    @config(priority=2)
    def dean_competition_detail_page(self, response):
        title= response.doc('font[size="5"]').text()
        detail = response.doc('td[style="line-height: 150%"]').text()
        publishdate = response.save['publishdate']
        publishdate = datetime.strptime(publishdate , '%Y-%m-%d %H:%M:%S')
        if publishdate >= limdate:
            return  {
                "title": title,
                "publishdate": publishdate.strftime('%Y-%m-%d'),
                "detail": detail,
            }


    def on_result(self, result):
        if not result:
            return
        super(Handler, self).on_result(result)
        title = result['title']
        publishdate = result['publishdate']
        detail = result['detail']
        self.cursor.execute('SELECT 1 FROM Competition WHERE title=%s LIMIT 1', title)  # 插入前判断是否存在
        if len(cursor.fetchall()) == 0:
            self.cursor.execute(
                'INSERT INTO Competition(title, publishdate, detail) VALUES (%s, %s, %s)',
                (title, publishdate, detail))
            self.conn.commit()
            print('insert success!')
        else:
            print('data has already exists.')

