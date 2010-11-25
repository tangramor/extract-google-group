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
import logging

from ExtractGoogleGroup import Extract
from string import Template


def Transform(startpage, endpage):
    forumId = 36        #the forum id to import these data into
    author = 'admin'    #the user that used to import data
    authorId = 1        #the user id of the user

    j = 1   #j is counter for threads
    k = 1   #k is counter for posts
    
    filesurfix = '_' + str(startpage) + '_' + str(endpage)
    threadsFileName = 'discuzx_threads' + filesurfix + '.sql'
    postsFileName = 'discuzx_posts' + filesurfix + '.sql'
    postTableidFileName = 'discuzx_post_tableid' + filesurfix + '.sql'

    f_threads = open(threadsFileName, 'w')
    f_posts = open(postsFileName, 'w')
    f_post_tableid = open(postTableidFileName, 'w')

    threadHeader = u"INSERT INTO `bbsers_forum_thread` (`tid`, `fid`, `posttableid`, `typeid`, `sortid`, `readperm`, `price`, `author`, `authorid`, `subject`, `dateline`, `lastpost`, `lastposter`, `views`, `replies`, `displayorder`, `highlight`, `digest`, `rate`, `special`, `attachment`, `moderated`, `closed`, `stickreply`, `recommends`, `recommend_add`, `recommend_sub`, `heats`, `status`, `isgroup`, `favtimes`, `sharetimes`, `stamp`, `icon`, `pushedaid`) VALUES \n"

    threadT = Template(u"""(${threadId}, ${forumId}, 0, 0, 0, 0, 0, '${author}', ${authorId}, '${subject}', ${dateline}, ${lastpost}, '${lastposter}', 0, ${replies}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0),\n""")

    postHeader = u"INSERT INTO `bbsers_forum_post` (`pid`, `fid`, `tid`, `first`, `author`, `authorid`, `subject`, `dateline`, `message`, `useip`, `invisible`, `anonymous`, `usesig`, `htmlon`, `bbcodeoff`, `smileyoff`, `parseurloff`, `attachment`, `rate`, `ratetimes`, `status`, `tags`, `comment`) VALUES \n"

    postT = Template(u"""(${postId}, ${forumId}, ${threadId}, ${first}, '${author}', ${authorId}, '${subject}', ${dateline}, '${message}', '${useip}', 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 0, '', 0),\n""")

    postTableidHeader = u"INSERT INTO `bbsers_forum_post_tableid` (`pid`) VALUES \n"

    postTableidT = Template(u"""(${postId}),\n""")

    f_threads.write(threadHeader)
    f_posts.write(postHeader)
    f_post_tableid.write(postTableidHeader)

    f_threads.close()
    f_posts.close()
    f_post_tableid.close()

    f_threads = open(threadsFileName, 'a')
    f_posts = open(postsFileName, 'a')
    f_post_tableid = open(postTableidFileName, 'a')
    
    r_list = range(startpage, endpage)

    for i in r_list:
        threads = u''
        posts = u''
        post_tableids = u''

        list = extract.getTopicAndUrlInTopicListPage(i)  
        for topics in extract.getTopicContentInTopicListPage(list):

            poster = u"原帖作者：<b>" + topics['from'] + u" &lt;" + topics['email'] + u"&gt;</b><br>\n发表时间：<b>" + topics['date'] + u"</b><br />\n原帖链接：<a href=\"" + extract.rootUrl + topics['individual_link'] + "\" target=_blank>" + extract.rootUrl + topics['individual_link'] + "</a><br /><br />\n"
            posts += postT.substitute(postId = k,
                forumId = forumId,
                threadId = j,
                first = 1,
                author = author,
                authorId = authorId,
                subject = topics['subject'],
                dateline = extract.dateToTimestamp(topics['date']),
                message = poster + topics['content'].replace("'", "\'"),
                useip = u'127.0.0.1'
                )
            post_tableids += postTableidT.substitute(postId = k)
            k += 1

            lastpost = extract.dateToTimestamp(topics['date'])
            if topics['replies']:
                for reply in topics['replies']:
                    lastpost = extract.dateToTimestamp(reply['date'])
                    poster = u"原帖作者：<b>" + reply['from'] + u" &lt;" + reply['email'] + u"&gt;</b><br>\n发表时间：<b>" + reply['date'] + u"</b><br />\n原帖链接：<a href=\"" + extract.rootUrl + reply['link'] + "\" target=_blank>" + extract.rootUrl + reply['link'] + "</a><br /><br />\n"
                    #print reply['content'].encode('utf8')
                    posts += postT.substitute(postId = k,
                        forumId = forumId,
                        threadId = j,
                        first = 0,
                        author = author,
                        authorId = authorId,
                        subject = reply['subject'],
                        dateline = lastpost,
                        message = poster + reply['content'].replace("'", "\'"),
                        useip = u'127.0.0.1'
                        )
                    post_tableids += postTableidT.substitute(postId = k)
                    k += 1

            threads += threadT.substitute(threadId = j,
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

        f_threads.write(threads.encode('utf8'))
        f_posts.write(posts.encode('utf8'))
        f_post_tableid.write(post_tableids)


    f_threads.close()
    f_posts.close()
    f_post_tableid.close()



logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='extract-google-group.log',
                    filemode='w');
                    
usage = "Usage: GoogleGroupToDiscuzSql groupname [-s startpage -e endpage]"

if sys.argv[1] == '--help' or sys.argv[1] == '-h':
    print usage

elif len(sys.argv) == 2:
    # call extract-google-group
    extract = Extract(sys.argv[1])
    startpage = 0
    endpage = extract.getTotalTopicListPageNumber(extract.getTotalTopicNumber())
    Transform(startpage, endpage)    

elif len(sys.argv) == 6:
    extract = Extract(sys.argv[1])
    startpage = int(sys.argv[3])
    endpage = int(sys.argv[5])
    Transform(startpage, endpage)
    
else:
    print usage
    
