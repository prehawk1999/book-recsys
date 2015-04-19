#coding=utf-8
import pymongo
# import logging
from pymongo import MongoClient
import web


# mongo数据库配置
conn = MongoClient('localhost',27017) 
db = conn.group_mems

# 有缓存的数据库类，第一次访问的信息会被保存下来
class RecsysDatabase(object):

    def __init__(self):
        self.books_info   = {}
        self.users_info   = {}
        # self.umodel_info  = {}
        self.tags_info    = {}

    def findOneBook(self, book_id):
        if book_id in self.books_info:
            return self.books_info[book_id]
        else:
            book = db.books.find_one({"id":book_id})
            if book and 'title' in book:
                self.books_info[book_id] = book
                return book

    def findOneUser(self, user_id):
        if user_id in self.users_info:
            return self.users_info[user_id]
        else:
            user = db.users.find_one({"user_id":user_id})
            if user:
                self.users_info[user_id] = user
                return user

    def findOneTag(self, tag_id):
        if tag_id in self.tags_info:
            return self.tags_info[tag_id]
        else:
            tag = db.tags.find_one({"name":tag_id})
            if tag:
                self.tags_info[tag_id] = tag
                return tag

    def findOneModel(self, mod_id):
        if mod_id in self.umodel_info:
            return self.umodel_info[mod_id]
        else:
            mod = db.umodel.find_one({"user_id":mod_id})
            if mod:
                self.umodel_info[mod_id] = mod
                return mod

rsdb = RecsysDatabase()

urls = (
	'/', 'index',
	'/book/(\d+)', 'book', 
	'/user/(\d+)', 'user',
	'/tag/(\d+)', 'tag', 
    '/login', 'login',
    '/logout', 'logout',
    '/register', 'register',
)

render = web.template.render('templates/')
web.config.debug = False
app = web.application(urls, locals())
session = web.session.Session(app, web.session.DiskStore('sessions'))  


class index(object):
	def GET(self, name='prehawk'):
		return render.index(name)

class book(object):
	def GET(self, book_id):
		# return '<p>%s</p>' % book_id
		book_info = rsdb.findOneBook(book_id)
		return render.book(book_info)

class user(object):
	pass

class tag(object):
	pass

class login(object):
	pass

class logout(object):
	pass

class register(object):
	pass

if __name__ == '__main__':
	app.run()