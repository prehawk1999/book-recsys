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
        self.users_info       = {}
        self.book_popular     = []
        self.book_recommend   = []
        self.book_domain      = {}
        self.book_tagged      = {}

    def summaryString(self, inpStr, num=12, dotlen=6):
        if num > 0 and len(inpStr) > num:
            return inpStr[:num] + '.'*dotlen
        else:
            return inpStr

    def summaryBook(self, book, ti_s=8, au_s=6, su_s=24, ta_s=12):
        book['title']      = self.summaryString(book['title'], ti_s, 2).strip()
        book['author']     = self.summaryString( ','.join(book['author']), au_s).strip()
        book['translator'] = self.summaryString( ','.join(book['translator']), au_s).strip()
        book['summary'] = self.summaryString(book['summary'], su_s).strip()
        # print book['tags']
        book['tags']    = self.summaryString( '/'.join([ x['name'] for x in book['tags'] ]), ta_s)
        return book

    def prettifyText(self, text):
        output = text.replace(u'\n', u'</p><p>')
        # print u'<p>' + output + u'</p>'
        return u'<p>' + output + u'</p>'


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

        umodel = db.umodel.find_one({"user_id":name})
        # print umodel
        if not umodel or 'interest_recbooks' not in umodel:
            return

        for b in umodel['interest_recbooks']:
            book = self.findOneBook(b[0]).copy()
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

    def findOneUser(self, user_id):
        if user_id in self.users_info:
            return self.users_info[user_id]
        else:
            user = db.users.find_one({"user_id":user_id})
            if user:
                self.users_info[user_id] = user
                return user

    def findTagBooks(self, tagname):
        if tagname in self.book_tagged:
            return self.book_tagged[tagname]

        self.book_tagged[tagname] = []

        def tbSort(a,b):
            aidx = a['tags'].split('/').index(tagname)
            bidx = b['tags'].split('/').index(tagname)
            if aidx < bidx:
                return 1
            elif aidx == bidx:
                if a['rating']['numRaters'] > b['rating']['numRaters']:
                    return 1
                elif a['rating']['numRaters'] == b['rating']['numRaters']:
                    if a['rating']['average'] > b['rating']['average']:
                        return 1
                    else:
                        return -1
                else:
                    return -1
            else:
                return -1

        for book in db.popbooks.find():
            if 'tags' in book and tagname in [x['name'] for x in book['tags']]:
                self.book_tagged[tagname].append(self.summaryBook(book, ta_s=100, su_s=200))
        self.book_tagged[tagname].sort(cmp=tbSort, reverse=True)

        return self.book_tagged[tagname]

class BaseHandler(tornado.web.RequestHandler):
    pass

class MainHandler(BaseHandler):
    def get(self):
        pb = rsdb.getPopbooks(60)
        pd = rsdb.getDombooks(10)
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            # print name
            rb = rsdb.getRecbooks(name)[:20]
        else:
            name = None
            rb = None

        self.render("index.html", username=name, popbooks=pb, recbooks=rb, dombooks=pd)

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', username=None)
    def post(self):
        # 这里补充一个，获取用户输入
        username = self.get_argument("username")
        password = self.get_argument("password")
        user = rsdb.findOneUser(username)
        if user:
            if ('crawled' in user and password == u'123456') or ('password' in user and password == user['password']):
                self.set_cookie('user', username)
                self.redirect('/')


class BookHandler(BaseHandler):
    
    def get(self, book_id):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None
        dbooks = rsdb.getDombooks(10)
        ret = rsdb.findOneBook(book_id).copy()
        ret['origin_title'] = ret['origin_title'].strip()
        ret['summary'] = rsdb.prettifyText(ret['summary'])
        ret['author_intro'] = rsdb.prettifyText(ret['author_intro'])
        ret['catalog'] = rsdb.prettifyText(ret['catalog'])
        return self.render("book.html", username=name, dombooks=dbooks,
            book_info=rsdb.summaryBook(ret, au_s=14, ta_s=34, su_s=-1))

class UserHandler(BaseHandler):
    
    def get(self):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None
        dbooks = rsdb.getDombooks(10)
        user = rsdb.findOneUser(name)
        for h in user['history'][:45]:
            if 'book_id' not in h:
                continue
            book = rsdb.findOneBook(h['book_id']).copy()
            h['book'] = rsdb.summaryBook(book)
        self.render('user.html', username = name, dombooks=dbooks, userinfo=user)


class TagHandler(BaseHandler):

    def get(self, tagname):
        if tagname:
            tagname = tagname.decode('utf-8')
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None
        tbooks = rsdb.findTagBooks(tagname)[:45]
        dbooks = rsdb.getDombooks(10)
        return self.render('tag.html', tagname=tagname, username=name, tagbooks=tbooks, dombooks=dbooks)

    def post(self):
        tagname = self.get_argument('tagname')
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None

        tbooks = rsdb.findTagBooks(tagname)[:45]
        dbooks = rsdb.getDombooks(10)
        return self.render('tag.html', tagname=tagname, username=name, tagbooks=tbooks, dombooks=dbooks)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')

class RegisterHandler(BaseHandler):
    
    def get(self):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None        
        self.render('register.html', username=name)

    def post(self):
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
    (r'/user', UserHandler),
    (r'/tag', TagHandler),
    (r'/tag/(.*)', TagHandler),
    (r'/login', LoginHandler),
    (r'/logout', LogoutHandler),
    (r'/register', RegisterHandler),
], **settings)

if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()