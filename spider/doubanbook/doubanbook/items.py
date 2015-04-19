# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class GroupItem(scrapy.Item):
    group_id = scrapy.Field()
    user_count = scrapy.Field()
    users = scrapy.Field() # a list of MemberItem

class MemberItem(scrapy.Item):
    user_id = scrapy.Field()
    read    = scrapy.Field()   # total read number from home page.
    crawled = scrapy.Field()   # bool, indicated that user has been first crawled
    # book_count = scrapy.Field()
    # books = scrapy.Field() # a list of bookid 
    # crawled = scrapy.Field()
    
class RateItem(scrapy.Item):
    user_id = scrapy.Field()
    book_id = scrapy.Field()
    rate = scrapy.Field()
    date = scrapy.Field()
    tags = scrapy.Field()
    comment = scrapy.Field()

class BookItem(scrapy.Item):
    info = scrapy.Field()


class HistoryItem(scrapy.Item):
    user_id  = scrapy.Field()
    collects = scrapy.Field()
    errstr   = scrapy.Field()