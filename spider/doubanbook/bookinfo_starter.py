# -*- coding: utf-8 -*-
import os,sys
import time
import random
import pymongo
from pymongo import MongoClient

from scrapy.crawler import Crawler
from scrapy import log, signals
from twisted.internet import reactor    
from doubanbook.spiders.user_books import UserBooksSpider
from scrapy.utils.project import get_project_settings

GAP = 20
conn = MongoClient('localhost',27017) 
db = conn.group_mems
allusers = [x for x in db.users.find({})]
#random.shuffle(allusers)
slice_n = len(allusers) / GAP
slice_l = len(allusers) % GAP
books_in_db = db.books.find({}, {"id":1})

def start_single_crawl():
    for user in db.users.find(timeout=False):
        if 'history' in user and user['read'] > 400 and user['read'] - len(user['history']) > 0:
            ret = os.system('cd /home/prehawk/windows/proj/book-recsys-crawler/doubanbook && /bin/python /usr/bin/scrapy crawl user_books -a uid=%s' % user['user_id'])
            #pstr = 'user_id: %s, read: %d, read_in_db: %d' % (user['user_id'], user['read'], len(user['history']))
            #print pstr
            print '====scrapy return value:', ret, '===='
            time.sleep(120)

if __name__ == '__main__':
    start_single_crawl()