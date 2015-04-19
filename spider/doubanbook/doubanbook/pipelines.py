# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import datetime
import pymongo
from pymongo import MongoClient
from scrapy.exceptions import DropItem

from doubanbook.spiders import *
from doubanbook.items import *


conn = MongoClient('localhost',27017) 
db = conn.group_mems

class DoubanbookPipeline(object):

    def __init__(self):
        self.still_start_urls = []
        pass

    def process_item(self, item, spider):
        if isinstance(item, MemberItem):
            updoc = db.users.find_one({"user_id":item['user_id']})
            if updoc:
                updoc['crawled'] = item['crawled']
                updoc['read']    = item['read']
                updoc['uptime']  = datetime.datetime.utcnow()
                db.users.update({"user_id":item['user_id']}, updoc, upsert=True)
                print 'mongodb: updating %s with %d read' % (item['user_id'], item['read'])
        elif isinstance(item, RateItem):
            db.users.update({"user_id":item['user_id']}, {"$addToSet":{"history":dict(item)}})
        elif isinstance(item, BookItem):
            db.books.update({'id':item['info']['id']}, dict(item['info']), upsert=True)
            #print 'mongodb: adding << %s >> ' % item['info']['id']
        elif isinstance(item, HistoryItem):
            pass

    def open_spider(self, spider):
        users_in_db = db.users.find({})
        if isinstance(spider, group_mems.GroupMemsSpider):   
            for u in users_in_db:
                spider.users.add(u['user_id'])
            spider.prime_size = len(spider.users)
        elif isinstance(spider, user_books.UserBooksSpider):
            for b in db.books.find({}, {"id":1}):
                spider.books.add(b['id'])

            for u in users_in_db: 
                delta = datetime.datetime.utcnow() - u['uptime'] 
                if u['crawled'] == 1 or ( delta.days > 0 and u['read'] > 15 ):
                    url = 'http://book.douban.com/people/%s/' % u['user_id']
                    if 'history' in u:
                        spider.read_in_db[u['user_id']] = len(u['history'])
                    elif u['crawled'] == 0:
                        spider.read_in_db[u['user_id']] = -1
                    else:
                        spider.read_in_db[u['user_id']] = 0

                    # if spider.read_in_db[u['user_id']] - u['read'] != 0:
                    #     print '%d, collects %d/%d' % (u['crawled'], spider.read_in_db[u['user_id']], u['read'])
            # 剩下的重试很多次还存在的初始链接应该是不存在用户了            
            #print '=== start_urls: %d ===' % len(spider.start_urls)

    def close_spider(self, spider):
        pass