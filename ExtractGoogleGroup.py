#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script extracts entries from a google group to a XML file
Require 'BeautifulSoup' module
Released under the GPL. Report bugs to tattoo@bbsers.org

(c) Wang Jun Hua, homepage: http://blog.bbsers.org/tattoo
General Public License: http://www.gnu.org/copyleft/gpl.html
"""

__VERSION__="0.1"

import string
import sys
import os
import codecs
import xmlrpclib
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup,Tag,CData
import re
import logging
from datetime import datetime
from datetime import timedelta
import time
from optparse import OptionParser
from string import Template
import pickle
import xml
from xml.sax import saxutils


class Extract:
    def __init__(self, name):
        self.groupname = name

        #基本URL，第一个命令行参数应该是Google Group的名称
        self.rootUrl = "https://groups.google.com"
        self.baseUrl = self.rootUrl + "/group/" + self.groupname + "/"
    
        #每页主题列表数目Google缺省设置为30条
        self.topicNumPerPage = 30      


    #取得页面源码并返回soup对象
    def _fetchPage(self, url):
        logging.info("begin fetch page %s",url)
        req = urllib2.Request(url)
        req.add_header('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.5) Gecko/20070713 Firefox/2.0.0.5')
        page = urllib2.build_opener().open(req).read()
        logging.info("fetch page successfully")
        return BeautifulSoup(page)
    
    def testFetchPage(self):
        print self._fetchPage(self.baseUrl)


    #取得主题总数
    def getTotalTopicNumber(self):
        url = self.baseUrl + "topics?tsc=1"
        soup = self._fetchPage(url)
        b = soup.find('div', {'class' : 'maincontbox'})
        b = b.find('span')
        b = b.findAll('b')[2]

        return b.string
    
    #取得当前google group的主题总数
    def _totalTopicNumber(self):
        self.totalTopicNumber = int(self.getTotalTopicNumber())
    
    def testGetTotalTopicNumber(self):
        self._totalTopicNumber()
        print self.totalTopicNumber
    
    
    #取得主题列表的页数，Google Group缺省是30个主题一页
    def getTotalTopicListPageNumber(self, topicNumber):
        iNumber = int(topicNumber)
        if (iNumber % self.topicNumPerPage) > 0:
            return iNumber / self.topicNumPerPage + 1
        else:
            return iNumber / self.topicNumPerPage
    
    #取得当前google group的主题列表页数
    def _totalTopicListPageNumber(self):
        self._totalTopicNumber()
        self.totalTopicListPageNumber = self.getTotalTopicListPageNumber(self.totalTopicNumber)
    
    def testGetTotalTopicListPageNumber(self):
        self._totalTopicListPageNumber()
        print self.totalTopicListPageNumber
    
    
    def _setup(self):
        self._totalTopicNumber()
        self._totalTopicListPageNumber()
        
    
    #去到第x页主题列表并返回页面soup对象
    def goToTopicListPage(self, page):
        self._setup()
        if page < self.totalTopicListPageNumber:
            url = self.baseUrl + "topics?start=" + str(page * self.topicNumPerPage) + "&sa=N"
            return self._fetchPage(url)
        elif page == self.totalTopicListPageNumber:
            url = self.baseUrl + "topics?start=" + str(self.totalTopicNumber) + "&sa=N"
            return self._fetchPage(url)
        else:
            return ""
    
    def testGoToTopicListPage(self):
        self._totalTopicListPageNumber()
        print self.goToTopicListPage(self.totalTopicListPageNumber)
    
    
    #取得一个主题列表内所有主题的标题和链接
    def getTopicAndUrlInTopicListPage(self, page):
        list = []
        
        b = self.goToTopicListPage(page)
        b = b.find('div', {'class' : 'maincontoutboxatt'})
        b = b.findAll('table')
    
        if b:
            for tpTbl in b:
                entry = {'subject':'', 'link':''}
                tmp = tpTbl.findAll('a')[1]
                entry['link'] = self.rootUrl + tmp['href']
                entry['subject'] = tmp.find('font').string
                list.append(entry)
        return list
    
    def testGetTopicAndUrlInTopicListPage(self):
        self._totalTopicListPageNumber()
        print self.getTopicAndUrlInTopicListPage(self.totalTopicListPageNumber)
    
    
    #给内容字符串中的链接添加前缀"https://groups.google.com"
    def _addPrefixToUrl(self, s):
        return s.replace("href=\"/", "href=\"" + self.rootUrl + "/")
    
    def testAddPrefixToUrl(self):
        logging.info("Test add <a href=\"/group/bbser/about\"> here!\n" + self._addPrefixToUrl("Test add <a href=\"/group/bbser/about\"> here!"))
        print self._addPrefixToUrl("Test add <a href=\"/group/bbser/about\"> here!")
    
    
    #取得一个主题列表页内所有主题的内容
    def getTopicContentInTopicListPage(self, list):
        """
        Structure of a topic
        topic
        |-from (author)
        |-email
        |-date
        |-subject
        |-content
        |-topiclink
        |-individual_link (the link only to this paste)
        |-replies
            |-id
            |-from (replier)
            |-email
            |-date
            |-subject (often is "Re: $subject")
            |-content
            |-link (the link only to this paste)
        """
        topics = []
        
        for entry in list:
            threads = {'from':'', 'email':'', 'date':'', 'subject':'','content':'', 'topiclink':'', 'individual_link':'', 'replies':[]}
            threads['topiclink'] = entry['link']
            threads['subject'] = entry['subject']
    
            topicPage = self._fetchPage(entry['link'])
            heads = topicPage.findAll('div', {'id' : 'oh'})
            bodies = topicPage.findAll('div', {'id' : 'inbdy'})
    
            for i in range(len(heads)):
                head = heads[i]
                body = bodies[i]
                
                #1楼
                if i == 0:
                    tmp = head.findAll('div')
                    fromtext = tmp[2].find('b').contents
                    if fromtext[0].find('&quot;') != -1:
                        nameAndMail = fromtext[0].split('&quot;')
                        author = nameAndMail[1]
                        email = self._addPrefixToUrl((str(nameAndMail[2]).replace("&lt;", "")) + (str(fromtext[1])) + (str(fromtext[2]).replace("&gt;", ""))).lstrip()
                    else:
                        email = self._addPrefixToUrl(str(fromtext[0]) + (str(fromtext[1])) + str(fromtext[2])).lstrip()
                        author = email
    
                    link = self._addPrefixToUrl(tmp[6].findAll('a')[3]['href'])
    
                    threads['from'] = author
                    threads['email'] = email
                    threads['date'] = tmp[4].find('b').string
                    content = self._addPrefixToUrl(str(body.contents))
                    threads['content'] = content
                    threads['individual_link'] = link
                else:
                    reply = {'id':'', 'from':'', 'email':'', 'date':'', 'subject':'','content':'', 'link':''}
    
                    tmp = head.findAll('div')
                    fromtext = tmp[2].find('b').contents
                    if fromtext[0].find('&quot;') != -1 :
                        nameAndMail = fromtext[0].split('&quot;')
                        author = nameAndMail[1]
                        email = self._addPrefixToUrl((str(nameAndMail[2]).replace("&lt;", "")) + (str(fromtext[1])) + (str(fromtext[2]).replace("&gt;", ""))).lstrip()
                    else:
                        email = self._addPrefixToUrl(str(fromtext[0]) + (str(fromtext[1])) + str(fromtext[2])).lstrip()
                        author = email
    
                    subject = str(tmp[5].find('b').contents)
                    link = self._addPrefixToUrl(tmp[6].findAll('a')[3]['href'])
                    
                    reply['id'] = i
                    reply['from'] = author
                    reply['email'] = email
                    reply['date'] = tmp[4].find('b').string
                    reply['subject'] = subject
                    content = self._addPrefixToUrl(str(body.contents))
                    reply['content'] = content
    
                    threads['replies'].append(reply)
                
                i += 1
    
            #threads['replies'].reverse()
            topics.append(threads)
    
        return topics
    
    def testGetTopicContentInTopicListPage(self):
        self._totalTopicListPageNumber()
        print self.getTopicContentInTopicListPage(self.getTopicAndUrlInTopicListPage(self.totalTopicListPageNumber))
    
    

#---------------------------------方法测试---------------------------------
test = Extract("bbser")

#test.testGetTotalTopicNumber()
#test.testGetTotalTopicListPageNumber()
#test.testGoToTopicListPage()
#test.testGetTopicAndUrlInTopicListPage()
#test.testAddPrefixToUrl()
test.testGetTopicContentInTopicListPage()



