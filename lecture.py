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
              time datetime,
              place VARCHAR(100),
              speaker VARCHAR(100),
              speakerbrif TEXT,
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

    def swjtu_page(self, response):
        for each in response.doc('[cmsid="34403899"] a').items():
            self.crawl(each.attr.href, callback=self.swjtu_detail_page)
        currentpage = response.doc('div.page_blue span.current').text()
        if int(currentpage) <= 7:
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

    def handleTime(self, text):
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
            'INSERT INTO Lecture(title, time, place, speaker, speakerbrif, detail) VALUES (%s, %s, %s, %s, %s, %s)',
            (title, time, place, speaker, speakerbrif, detail))
        self.conn.commit()
        print('insert success!')
