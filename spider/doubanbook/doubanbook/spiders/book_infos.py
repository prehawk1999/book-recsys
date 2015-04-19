# -*- coding: utf-8 -*-
import scrapy
import json

from scrapy.selector import Selector
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.utils.url import urljoin_rfc
from doubanbook.items import *
from scrapy.exceptions import CloseSpider

import pymongo
from pymongo import MongoClient

conn = MongoClient('localhost',27017) 
db = conn.group_mems

class BookInfosSpider(scrapy.Spider):

    name = "book_infos"
    allowed_domains = ["douban.com"]
    start_urls = ['https://api.douban.com/v2/book/%s' % b['id'] for b in db.books.find() if 'title' not in b]
    handle_httpstatus_list = [403]
    count = 0

    def parse(self, response):
        if response.status == 200:
            bt = BookItem()
            #self.book_count += 1
            book_info = json.loads(response.body)
            bt['info'] = book_info
            self.count += 1
            self.log('add info in book << %s >>, totally %d books ' % (book_info['id'], self.count), 
                level=scrapy.log.INFO)
            yield bt
        elif response.status == 403:
            self.log('api limit exceeded.', level=scrapy.log.INFO)
            raise CloseSpider('api limit exceeded.')
            return
