#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Created on 2017-03-28 22:14:07
# Project: LecturePush

from pyspider.libs.base_handler import *
import re
from datetime import datetime
from pyspider.libs.base_handler import *
import pymysql

conn = pymysql.connect(host='ip', user='root', passwd='password', db='db',
                       charset="utf8")
cursor = conn.cursor()
from lxml import etree
from tidylib import tidy_document
import urllib2,cookielib,re,jieba


limdate = 20160900#日期下限


def iopen(url):
  cookie = cookielib.CookieJar()
  handler = urllib2.HTTPCookieProcessor(cookie)
  opener = urllib2.build_opener(handler)
  # 将cookies绑定到一个opener cookie由cookielib自动管理
  header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:51.0) Gecko/20100101 Firefox/51.0'
  }
  request = urllib2.Request(url,'',header)
  # 构造request请求
  html = opener.open(request).read().decode('utf8')
  return html
def deletetabnenter(string):
  #print 'deletetabnenter\t'
  newstring = ''
  for char in string:
    if re.match('[ \n\t“”"、+（）()]'.decode('utf8'),char) == None and char != u'\xa0':
      newstring += char
  return newstring

class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', }

    }

    def __init__(self):
        self.conn = conn
        self.cursor = cursor
        sql = '''
            CREATE TABLE IF NOT EXISTS Lecture(
              id INT PRIMARY KEY AUTO_INCREMENT,
              title VARCHAR(100),
              lecturetime datetime,
              place VARCHAR(100),
              speaker VARCHAR(100),
              speakerbrif TEXT,
              detail TEXT
        )ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;'''
        sql = '''
            CREATE TABLE IF NOT EXISTS Matches(
              id INT PRIMARY KEY AUTO_INCREMENT,
              title VARCHAR(100),
              matchtime datetime,
              detail TEXT
        )ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;'''
        self.cursor.execute(sql)
        self.conn.commit()

    @every(minutes=3 * 60)
    def on_start(self):
        self.crawl(
            'http://www.swjtu.edu.cn/jsp/activity.jsp?page=1&siteId=12163&catalogPath=-12163-12259-&selectDay=&searchType=month&address=&keyword=&hdType=',
            callback=self.swjtu_page, validate_cert=False, auto_recrawl=True)
        self.crawl('http://dean.swjtu.edu.cn/servlet/LectureAction?Action=LectureMore&SelectType=Month',
                   callback=self.dean_page, validate_cert=False, auto_recrawl=True)
        #match(self)

    def swjtu_page(self, response):
        for each in response.doc('[cmsid="34403899"] a').items():
            self.crawl(each.attr.href, callback=self.swjtu_detail_page)
        currentpage = response.doc('div.page_blue span.current').text()
        if not currentpage and int(currentpage) <= 7:
            for each in response.doc('.page_blue a').items():
                if (each.text() == '>>'):
                    self.crawl(each.attr.href, callback=self.swjtu_page)

    def dean_page(self, response):
        html = response.doc('script')
        lecture_pages = re.findall('var allPage = "(.*?)"', html.text(), re.S)[0]
        for each in response.doc('[style="float:left;width:735px;"] a').items():
            self.crawl(each.attr.href, callback=self.dean_detail_page)
        if lecture_pages > 1:
            for item in range(2, int(lecture_pages) + 1):
                lecture_page_link = 'http://dean.swjtu.edu.cn/servlet/LectureAction?Action=LectureMore&SelectType=Month&page={}'.format(
                    item)
                self.crawl(lecture_page_link, callback=self.dean_page)
                
    def match(self):
        a = etree.HTML(tidy_document(iopen('http://dean.swjtu.edu.cn/servlet/NewsView?NewsID=BEBF684C17BED733'))[0])
        b = etree.HTML(tidy_document(iopen('http://dean.swjtu.edu.cn/servlet/NewsView?NewsID=0C618242FA8B1810'))[0])
        tree = etree.HTML('<html></html>')
        tree.append(a)
        tree.append(b)
        tdlist = tree.xpath('/html/html/body/div/table/tr/td/div/table/tbody/tr/td[@width="286"]')[1:]
        textcluster = []
        for td in tdlist:
            textcluster.append(td.xpath('.//text()'))
        tmp = []
        for textlist in textcluster:
            name = ''
            for text in textlist:
                name += text
            if name.find('赛'.decode('utf8')) != -1:
                tmp.append(deletetabnenter(name))
        textlist = tmp
        textlist2 = textlist
        textcluster = []
        for text in textlist:
            tmp = jieba.lcut_for_search(text)
            tttmp = []
            for ttmp in tmp:
                if re.match('全国|大学|学生|大学生|竞赛|大赛|学院|创|与|挑战|作品|计划'.decode('utf8'),ttmp) == None:
                    tttmp.append(ttmp)
            textcluster.append(tttmp)
        url = 'http://dean.swjtu.edu.cn/servlet/NewsAction?Action=NewsMore&page='
        anchorlist = []
        page = 1
        while 1:
            html = tidy_document(iopen(url+str(page)))[0]
            tree = etree.HTML(html)
            lilist = tree.xpath('/html/body/div/div/ul/li')
            for li in lilist:
                name = deletetabnenter(li.xpath('./div/a/text()')[0])
                date = deletetabnenter(li.xpath('./div/text()')[2])
                url2 = deletetabnenter('http://dean.swjtu.edu.cn'+li.xpath('./div/a/@href')[0][2:])
                date = int(date[:4]+date[5:7]+date[8:])
                if date < limdate:
                    break
                if re.search('奖|绩|获|记|名单|课|结果|简报|中学生'.decode('utf8'),name) == None and name.find('赛'.decode('utf8')) != -1:
                    anchorlist.append([name,date,url2])
            if date < limdate:
                break
            page += 1
        _ = []
        for cursor in range(len(textlist2)):
            tmp = []
            for anchor in anchorlist:
                num = 0
                for text in textcluster[cursor]:
                    if anchor[0].find(text) != -1:
                        num += 1
                tmp.append(num)
            if max(tmp) > 1:
                for cs in range(len(tmp)):
                    if tmp[cs] > 1:
                        if _.count(anchorlist[cs]) == 0:
                            _.append(anchorlist[cs])
        for cursor in range(len(_)-1):
            for cs in range(len(_)-1):
                if _[cs][1] < _[cs+1][1]:
                    tmp = _[cs+1]
                    _[cs+1] = _[cs]
                    _[cs] = tmp
        for __ in _:
            self.crawl(__[2], callback=self.match_detail_page)

    def handleTime(self, text):
        text = text.split('-')[0]
        timenum = re.sub("\D", "", text)
        time = datetime.strptime(timenum, '%Y%m%d%H%M')
        return time

    def deadTime(self, now):
        month = now.month - 2;  # 只爬取前两个月的
        if month < 1:
            month = month + 12
        return datetime.strptime(str(now.year) + str(month), '%Y%m')

    def close_crawl(self):
        pass

    @config(priority=2)
    def swjtu_detail_page(self, response):
        title = response.doc(
            '[style="width:545px; height:45px; float:left; line-height:40px; font-size:14px; color:#505050; font-weight:bold;"]').text()
        speakerbrief = response.doc(
            '[style="width:530px; height:45px; float:left; line-height:14px; font-size:12px; color:#505050;"]').text()
        speaker = response.doc(
            '[style="width:545px; height:21px; background:url(/themes/12163/default/images/xswnhd3.jpg) no-repeat; float:left;line-height:20px;"]').text()
        place = response.doc(
            '[style="width:545px; height:21px; background:url(/themes/12163/default/images/xswnhd4.jpg) no-repeat; float:left;line-height:20px;"]').text()
        date = response.doc(
            '[style="width:726px; height:40px; line-height:40px; text-align:left; margin:10px 0px 0px 16px; background:url(/themes/12163/default/images/xswnhd2.jpg);"]').text()
        time = response.doc(
            '[style="width:50px; height:80px; margin:10px auto; text-align:center; font-size:14px; font-weight:bold; line-height:23px; color:#6c6c6c;"]').text()
        time = self.handleTime(date + " " + time)
        detail = response.doc('[style="width:700px; height:auto; margin:0 auto;"]').text()

        deadtime = self.deadTime(datetime.now())
        if time >= deadtime:
            return {
                "title": title,
                "speaker": speaker,
                "speakerbrif": speakerbrief,
                "time": time.strftime('%Y-%m-%d %H:%M'),
                "detail": detail,
                "place": place,
            }

    @config(priority=2)
    def dean_detail_page(self, response):
        title = ""
        line = 0
        speakerbrief = ""
        time = datetime.now()
        place = ""
        speaker = ""
        detail = response.doc('table#table1 tr td').text()
        for each in response.doc('table#table1 tr td').items():
            if line == 0:
                title = each.text()
            if line == 3:
                time = self.handleTime(each.text())
            if line == 4:
                place = each.text()
            if line == 5:
                speaker = each.text()
            if line == 7:
                speakerbrief = each.text()
            line = line + 1
        deadtime = self.deadTime(datetime.now())
        if time >= deadtime:
            return {
                "title": title,
                "speaker": speaker,
                "speakerbrif": speakerbrief,
                "time": time.strftime('%Y-%m-%d %H:%M'),
                "detail": detail,
                "place": place,
            }

    @config(priority=2)
    def match_detail_page(self, response):
        title = ""
        line = 0
        time = datetime.now()
        detail = 
        deadtime = self.deadTime(datetime.now())
        if time >= deadtime:
            return {
                "title": title,
                "time": time.strftime('%Y-%m-%d %H:%M'),
                "detail": detail
            }

    def on_result(self, result):
        if not result:
            return
        super(Handler, self).on_result(result)
        title = result['title']
        time = result['time']
        place = result['place']
        speaker = result['speaker']
        speakerbrif = result['speakerbrif']
        detail = result['detail']

        self.cursor.execute(
            'INSERT INTO Lecture(title, lecturetime, place, speaker, speakerbrif, detail) VALUES (%s, %s, %s, %s, %s, %s)',
            (title, time, place, speaker, speakerbrif, detail))
        self.conn.commit()
        print('insert success!')
