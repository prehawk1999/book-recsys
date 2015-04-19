# -*- coding: utf-8 -*-
import re
import time
import scrapy

import json
from twisted.internet import defer, reactor
from scrapy.selector import Selector
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.utils.url import urljoin_rfc
from scrapy.exceptions import CloseSpider
from doubanbook.items import *


class UserBooksSpider(CrawlSpider):

    def __init__(self, myarg=None, *args, **kwargs):
        super(UserBooksSpider, self).__init__(*args, **kwargs)
        al = myarg.split('#')
        uid = al[0]
        self.page  = al[1]
        self.start_urls = ['http://book.douban.com/people/%s/' % uid]
        #print pg
        
    name = "user_books"
    allowed_domains = ["douban.com"]
    page = 0
    rules = []
    handle_httpstatus_list = [403]
    books = set()
    read_in_db = dict() # record the amount of collects of a user that has been crawled.

    book_count = 0
    def parse_start_url(self, response):
        if response.status == 403:
            raise CloseSpider('meet blocking! parse_start_url')
            self.log('meet blocking!', level=scrapy.log.WARNING)
            return
        sel = Selector(response)
        label = sel.xpath('//*[@id="content"]//*[@class="number-accumulated"]//*[@class="number-label"]/text()').extract()
        read = sel.xpath('//*[@id="content"]//*[@class="number-accumulated"]//*[@class="number"]/text()').extract()
       
        if label and label[0] == u'读过':
            read = int(read[0])
            #print 'a'
        else:
            read = 0
            #print 'b'
        #print label, read
        #d = defer.Deferred()
        #reactor.callLater(pause, d.callback, (x, pause))
        mem = MemberItem()  
        user_id = re.search(r'http://book.douban.com/people/(\w+)/', response.url).group(1)
        mem['user_id'] = user_id
        mem['crawled'] = 1
        mem['read']    = read
        #time.sleep(2)
        if read > self.read_in_db[user_id]:
            if self.read_in_db[user_id] == -1:
                self.log('Add @ %s with %d collects.' % (user_id, read), 
                    level=scrapy.log.INFO)
            else:
                self.log('Refresh @ %s with %d collects(%d recorded).' % (user_id, read, self.read_in_db[user_id]), 
                    level=scrapy.log.INFO)
            #mem['read'] = read # 更新阅读量
            #page_appendix = 'collect?start=%d&sort=time&rating=all&filter=all&mode=grid' % int(self.page)
            req = scrapy.Request(url=response.url + 'collect',#page_appendix, 
                callback=self.parse_user_collect)
            req.meta['user_id'] = user_id
            yield req
        else:
            #if self.read_in_db[user_id] > 0:
            #mem['read'] = read    # 更新阅读量        
            self.log('Ignore @ %s (saved)' % user_id, 
                level=scrapy.log.INFO)
        yield mem 


    def parse_user_collect(self, response):
        if response.status == 403:
            raise CloseSpider('meet blocking! parse_user_collect')
            self.log('meet blocking!', level=scrapy.log.WARNING)
            return
        meta = response.meta
        sel = Selector(response)
        collect = []
        for sub in sel.xpath('//*[@id="content"]//ul[@class="interest-list"]//li[@class="subject-item"]'):
            book_id   = sub.xpath('*[@class="pic"]/a/@href').re(r'http://book.douban.com/subject/(\w+)/')[0]
            book_name =  sub.xpath('*[@class="info"]//a/@title').extract()[0]
            #self.users[meta['user_id']]['book'].append(book_id)
            rt = RateItem()
            rt['user_id'] = meta['user_id']
            rt['book_id'] = book_id
            if book_id not in self.books:
                self.log('Add New book to mongodb: << %s >> (%d books)' % (book_id, len(self.books)), level=scrapy.log.INFO)
                self.books.add(book_id)
                bt = BookItem()
                book_empty = dict()
                book_empty['id'] =  book_id
                bt['info'] = book_empty
                yield bt
                # req = scrapy.Request(url='https://api.douban.com/v2/book/%s' % book_id, 
                #     callback=self.parse_book_page)
                # req.meta['book_id'] = book_id
                # yield req
            # else:
            #     self.log('Using Existed book: << %s >>' % book_id, level=scrapy.log.INFO)

            collect.append(book_id)

            rate = sub.xpath('*[@class="info"]/*[@class="short-note"]//span[1]/@class').re(r'\w+?([1-5])-t')
            if rate:
                rt['rate'] = rate[0]
            else:
                rt['rate'] = 0
            date = sub.xpath('*[@class="info"]/*[@class="short-note"]//*[@class="date"]/text()').re(r'(\d{4}-\d{2}-\d{2})\s+\w+')[0]
            if date:
                rt['date'] = date
            else:
                self.log('parse_user_collect date parse error!', 
                    level=scrapy.log.WARNING)
            tags = sub.xpath('*[@class="info"]/*[@class="short-note"]//*[@class="tags"]/text()').re(r'.*: (.*)')
            if tags:
                rt['tags'] = tags[0].split(' ')

            comment = sub.xpath('*[@class="info"]/*[@class="short-note"]/p/text()').extract()
            if comment == [u'\n  ']:
                rt['comment'] = None
            else:
                rt['comment'] = comment[0]

            yield rt

        
        self.log('get %d rate history with @ %s' % (len(collect), meta['user_id']), 
                level=scrapy.log.INFO)
        print response.url
        self.read_in_db[meta['user_id']] += len(collect)

        # 翻页
        next_page = sel.xpath('//*[@id="content"]//span[@class="next"]/a/@href').extract()
        if next_page: 
            req = scrapy.Request(url=next_page[0], callback=self.parse_user_collect)
            req.meta['user_id'] = meta['user_id']
            yield req
        else:
            # End of the pages.
            self.log(' === End @ %s with %d new collects(shown below) ===' % (meta['user_id'], len(collect)), 
                level=scrapy.log.INFO)
            self.log(' '.join(collect),
                level=scrapy.log.INFO)
            ht = HistoryItem()
            ht['user_id']  = meta['user_id']
            ht['errstr']   = ''
            ht['collects'] = len(collect)
            print repr(ht)
            yield ht

    def parse_book_page(self, response):
        meta = response.meta
        bt = BookItem()
        if response.status == 200:
            self.book_count += 1
            meta = response.meta
            book_info = json.loads(response.body)
            bt['info'] = book_info
        elif response.status == 403:
            # self.log('meet blocking! parse_book_page (%d crawled)' % self.book_count, 
            #     level=scrapy.log.INFO)
            book_empty = dict()
            book_empty['id'] =  meta['book_id']
            bt['info'] = book_empty
            #raise CloseSpider('meet blocking! parse_book_page (%d crawled)' % self.book_count)
        yield bt


