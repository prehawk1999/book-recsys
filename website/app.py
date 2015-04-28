#coding=utf-8
import os
import tornado.ioloop
import tornado.web
import pymongo
from pymongo import MongoClient
from bson import ObjectId

class RecsysDatabase:

    def __init__(self):
        self.books_info       = {}
        self.book_popular     = []
        self.book_recommend   = []
        self.book_domain      = {}

    def summaryString(self, inpStr, num=12, dotlen=6):
        if len(inpStr) > num:
            return inpStr[:num] + '.'*dotlen
        else:
            return inpStr

    def summaryBook(self, book):
        book['title']   = self.summaryString(book['title'], 6, 2)
        book['author']  = self.summaryString( ','.join(book['author']), 6 )
        book['summary'] = self.summaryString(book['summary'], 24)
        book['tags']    = self.summaryString( '/'.join([ x['name'] for x in book['tags'] ]), 12 )
        return book

    ## limit要是偶数
    def getPopbooks(self, limit=60):
        if self.book_popular:
            return self.book_popular

        for i,pb in enumerate( db.popbooks.find(limit=limit) ):
            if not pb or 'title' not in pb:
                continue
            pb = self.summaryBook(pb)

            if i%2 == 0:
                self.book_popular.append({'up':pb, 'down':{}})
            else:
                self.book_popular[len(self.book_popular)-1]['down'] = pb

        return self.book_popular

    def getRecbooks(self, name):
        if self.book_recommend:
            return self.book_recommend

        umodel = db.umodel.find({"user_id":name})
        if not umodel:
            return

        for b in umodel['interest_recbooks']:
            book = self.findOneBook(b['id'])
            if not book or 'title' not in book:
                continue
            self.book_recommend.append(self.summaryBook(book))
        return self.book_recommend

    def getDombooks(self, limit=10):
        if self.book_domain:
            return self.book_domain

        # self.book_domain = {}
        for book in db.popbooks.find():
            if 'general_domain' not in book or not book['general_domain']:
                continue
            dom = book['general_domain'][0][0]
            if dom not in self.book_domain:
                self.book_domain[dom] = []
            if len(self.book_domain[dom]) < limit:
                self.book_domain[dom].append(self.summaryBook(book))
        return self.book_domain

    def findOneBook(self, book_id):
        if book_id in self.books_info:
            return self.books_info[book_id]
        else:
            book = db.books.find_one({"id":book_id})
            if book and 'title' in book:
                self.books_info[book_id] = book
                return book

class BaseHandler(tornado.web.RequestHandler):
    # def get_current_user(self):
    #     return self.get_secure_cookie("user")
    pass

class MainHandler(BaseHandler):
    def get(self):
        pb = rsdb.getPopbooks(60)
        pd = rsdb.getDombooks(10)
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = getRecbooks(name)
        else:
            name = None
            rb = None

        self.render("index.html", username=name, popbooks=pb, recbooks=rb, dombooks=pd)


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
        # self.write('<html><body><form action="/login" method="post">'
        #            'Name: <input type="text" name="name">'
        #            '<input type="submit" value="Sign in">'
        #            '</form></body></html>')
    def post(self):
        # 这里补充一个，获取用户输入
        # self.get_argument("name")

        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")

class BookHandler(BaseHandler):
    
    def get(self, book_id):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None
        book_info = rsdb.findOneBook(book_id)
        return self.render("book.html", username=name, book_info=book_info)

class UserHandler(BaseHandler):
    pass

class TagHandler(BaseHandler):

    def get(self):
        pass

    def post(self):
        # self.write(self.get_argument())
        pass


class LogoutHandler(BaseHandler):
    def post(self):
        self.set_secure_cookie('user', '')

class RegisterHandler(BaseHandler):
    pass

# mongo数据库配置
conn = MongoClient('localhost',27017) 
db = conn.group_mems
rsdb = RecsysDatabase()

settings = {
    # "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__", # 安全cookie所需的
    # "login_url": "/login", # 默认的登陆页面，必须有
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_url_prefix": "/templates/",
    "debug":True
}

application = tornado.web.Application([
    (r'/', MainHandler),
    (r'/book/(\d+)', BookHandler),
    (r'/user/(\d+)', UserHandler),
    (r'/tag/(\d+)', TagHandler),
    (r'/login', LoginHandler),
    (r'/logout', LogoutHandler),
    (r'/register', RegisterHandler),
], **settings)

if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()