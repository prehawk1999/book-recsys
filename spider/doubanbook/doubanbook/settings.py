# -*- coding: utf-8 -*-

# Scrapy settings for doubanbook project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'doubanbook'

SPIDER_MODULES = ['doubanbook.spiders']
NEWSPIDER_MODULE = 'doubanbook.spiders'
DOWNLOAD_DELAY = 2
COOKIES_ENABLED = True
CONCURRENT_REQUESTS = 1
DOWNLOAD_TIMEOUT = 10

#AUTOTHROTTLE_ENABLED = True
#AUTOTHROTTLE_DEBUG = True


LOG_LEVEL = 'INFO'
DOWNLOADER_MIDDLEWARES = {
        'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware' : None,
        'doubanbook.comm.rotate_useragent.RotateUserAgentMiddleware' :400,
    }

ITEM_PIPELINES = {
    'doubanbook.pipelines.DoubanbookPipeline': 300,
}
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'doubanbook (+http://www.yourdomain.com)'
