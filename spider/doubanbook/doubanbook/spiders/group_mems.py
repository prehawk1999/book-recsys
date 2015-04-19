# -*- coding: utf-8 -*-
import scrapy

from scrapy.selector import Selector
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.utils.url import urljoin_rfc
from doubanbook.items import MemberItem, GroupItem

# 填入需要抓取的小组id
ids = ['ns', 'MLPR', 'MLPR', '27885', 'BigData', 'dm', '503043', '325827', 'User-behavior', 'socialcomputing'] # 299259

class GroupMemsSpider(CrawlSpider):
    
    name = "group_mems"
    allowed_domains = ["douban.com"]
    start_urls = ['http://www.douban.com/group/%s/members' % x for x in ids]
    #print start_urls[0]
    rules = [
            # 小组翻页规则
            Rule(LxmlLinkExtractor(allow = (r'/group/\w+/members\?start=\d+.*', ), unique = False), 
                callback = 'parse_group_page', follow = True,
                process_links = lambda links: [x for x in links if x.text == u'后页>']),
        ]

    users = set() # users = set()
    prime_size = 1
    user_count = 0
    crawl_count = 0

    def parse_start_url(self, response):
        sel = Selector(response)
        # self.group_id = sel.xpath('//*[@id="content"]//div[@class="title"]/a/@href').re(r'http://www.douban.com/group/(\w+)/.*')[0]
        #self.user_count = int(sel.xpath('//*[@id="content"]//span[@class="count"]/text()').re('(\d+)')[0])
        self.parse_group_page(response)

    def parse_group_page(self, response):
        sel = Selector(response) 
        for mem in sel.xpath('//div[@class="member-list"]//div[@class="name"]/a/@href'):
            self.crawl_count += 1
            m = mem.re('http://www.douban.com/group/people/(\w+)')
            if m and m[0] not in self.users:
                self.users.add(m[0])
                mem = MemberItem()
                mem['user_id'] = m[0]
                mem['read']    = 0
                mem['crawled'] = 0
                yield mem
        self.log('%d new users got(unique), totally %d members crawled' % (len(self.users) - self.prime_size, self.crawl_count), 
            level=scrapy.log.INFO)


