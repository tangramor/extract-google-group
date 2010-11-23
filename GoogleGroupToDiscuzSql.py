#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script extracts entries from a google group to a SQL file
that can be used by a DiscuzX 1.5 forum
Require 'BeautifulSoup' module
Released under the GPL. Report bugs to tattoo@bbsers.org

(c) Wang Jun Hua, homepage: http://blog.bbsers.org/tattoo
General Public License: http://www.gnu.org/copyleft/gpl.html
"""

__VERSION__="0.1"

import string
import sys
import os

from ExtractGoogleGroup import Extract
from string import Template

extract = Extract(sys.argv[1])

forumId = 36        #the forum id to import these data into
author = 'admin'    #the user that used to import data
authorId = 1        #the user id of the user

f_threads = open('discuzx_threads.sql', 'w')
f_posts = open('discuzx_posts.sql', 'w')

threadHeader = u"INSERT INTO `bbsers_forum_thread` (`tid`, `fid`, `posttableid`, `typeid`, `sortid`, `readperm`, `price`, `author`, `authorid`, `subject`, `dateline`, `lastpost`, `lastposter`, `views`, `replies`, `displayorder`, `highlight`, `digest`, `rate`, `special`, `attachment`, `moderated`, `closed`, `stickreply`, `recommends`, `recommend_add`, `recommend_sub`, `heats`, `status`, `isgroup`, `favtimes`, `sharetimes`, `stamp`, `icon`, `pushedaid`) VALUES \n"

threadT = Template(u"""(${threadId}, ${forumId}, 0, 0, 0, 0, 0, '${author}', ${authorId}, '${subject}', ${dateline}, ${lastpost}, '${lastposter}', 0, ${replies}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0),\n""")

postHeader = u"INSERT INTO `bbsers_forum_post` (`pid`, `fid`, `tid`, `first`, `author`, `authorid`, `subject`, `dateline`, `message`, `useip`, `invisible`, `anonymous`, `usesig`, `htmlon`, `bbcodeoff`, `smileyoff`, `parseurloff`, `attachment`, `rate`, `ratetimes`, `status`, `tags`, `comment`) VALUES \n"

postT = Template(u"""(${postId}, ${forumId}, ${threadId}, ${first}, '${author}', ${authorId}, '${subject}', ${dateline}, '${message}', '${useip}', 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 0, '', 0),\n""")

f_threads.write(threadHeader)
f_posts.write(postHeader)

f_threads.close()
f_posts.close()


f_threads = open('discuzx_threads.sql', 'a')
f_posts = open('discuzx_posts.sql', 'a')

threads = None
posts = None

j = 1   #j is counter for threads
k = 1   #k is counter for posts

for i in range(2): #extract.testGetTotalTopicListPageNumber():
    
    list = extract.getTopicAndUrlInTopicListPage(i)  
    for topics in extract.getTopicContentInTopicListPage(list):
        threadId = j + 5
        postId = k + 5
        lastpost = extract.dateToTimestamp(topics['date'])
        if topics['replies']:
            for reply in topics['replies']:
                postId += 1
                lastpost = extract.dateToTimestamp(reply['date'])
                poster = "<b>" + reply['from'] + "&lt;" + reply['email'] + "&gt;</b>\n"
                posts += postT.substitute(postId = postId,
                    forumId = forumId,
                    threadId = threadId,
                    first = 0,
                    author = author,
                    authorId = authorId,
                    subject = reply['subject'],
                    dateline = lastpost,
                    message = poster + reply['content'],
                    useip = '127.0.0.1'
                    )
                k += 1

        poster = "<b>" + topics['from'] + "&lt;" + topics['email'] + "&gt;</b>\n"
        posts += postT.substitute(postId = postId,
            forumId = forumId,
            threadId = threadId,
            first = 1,
            author = author,
            authorId = authorId,
            subject = topics['subject'],
            dateline = extract.dateToTimestamp(topics['date']),
            message = poster + topics['content'],
            useip = '127.0.0.1'
            )
        threads += threadT.substitute(threadId = threadId,
            forumId = forumId,
            author = author,
            authorId = authorId,
            subject = topics['subject'],
            dateline = extract.dateToTimestamp(topics['date']),
            lastpost = lastpost,
            lastposter = author,
            replies = len(topics['replies'])
            )

        j += 1



f_threads.close()
f_posts.close()


