#coding=utf-8
import os
import tornado.ioloop
import tornado.web
import datetime
import pymongo
from pymongo import MongoClient
from bson import ObjectId
import sys
sys.path.append('../engine/')

from AppModel import AppModel

class RecsysDatabase:

    def __init__(self):
        self.books_info       = {}
        self.users_info       = {}
        self.book_popular     = []
        self.book_recommend   = []
        self.book_domain      = {}
        self.book_tagged      = {}
        self.field_books      = {}

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
        self.book_recommend = []
        umodel = db.umodel.find_one({"user_id":name})
        if not umodel or 'interest_recbooks' not in umodel or not umodel['interest_recbooks']:
            user = db.users.find_one({"user_id":name})
            if 'website' not in user or len(user['history']) < 5:
                return
            # print 'start recommending.'
            books = model.getRecBooks(name)
            print len(books)
            self.book_recommend = [self.summaryBook(b) for b in books][:10]

        else:
            # print user['user_id']
            for b in umodel['interest_recbooks'][:10]:
                book = self.findOneBook(b[0]).copy()
                if not book or 'title' not in book:
                    continue
                self.book_recommend.append(self.summaryBook(book))
        return self.book_recommend

    def getFieldBooks(self, name, limit=10):
        umodel = db.umodel.find_one({"user_id":name})
        if not umodel or 'field_eval' not in umodel:
            return
        user = rsdb.findOneUser(name)
        if not user:
            return

        use_read = [x['book_id'] for x in user['history']]

        if not self.field_books:
            for f in db.fields.find():
                self.field_books[f['field']] = [self.summaryBook(b) for b in f['books']]

        f_vec = umodel['field_eval'].items()
        f_vec.sort(cmp=lambda a,b:cmp(a[1],b[1]),reverse=True)
        f_books = {}
        for f in f_vec:
            f_books[f[0]] = [x for x in self.field_books[f[0]] if x not in use_read][:10]
        return f_books


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

    def findOneBook(self, book_id, update=False):
        book = db.books.find_one({"id":book_id})
        if book and 'title' in book:
            self.books_info[book_id] = book
            return book

    def findOneUser(self, user_id):
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

    def insertUser(self, username, password):
        ret = db.users.find_one({"user_id":username})
        if not ret and username and password:
            user_doc = {'website':1,'user_id':username, 'password':password, 'history':[], 'uptime':datetime.datetime.utcnow()}
            db.users.insert(user_doc)
            print 'insert one user:%s, %s' % (username, password)

    def insertComment(self, comment, user_id, book_id):
        comment_doc = {}
        comment_doc['content'] = comment
        comment_doc['user_id'] = user_id
        comment_doc['date']    = datetime.datetime.utcnow()
        dbret = db.books.update({"id":book_id}, {"$push":{"comments":comment_doc}})
        print 'book comment inserted %s' % book_id
        if not dbret['ok']:
            print 'error update comments'

class BaseHandler(tornado.web.RequestHandler):
    pass

class MainHandler(BaseHandler):
    def get(self):
        pb = rsdb.getPopbooks(60)
        pd = rsdb.getDombooks(10)
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = rsdb.getRecbooks(name)
            fb = rsdb.getFieldBooks(name)
        else:
            name = None
            rb = None
            fb = None

        self.render("index.html", username=name, popbooks=pb, recbooks=rb, dombooks=pd, fieldbooks=fb)

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', username=None)
    
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        user = rsdb.findOneUser(username)
        if user:
            if ('crawled' in user and password == u'123456') or ('password' in user and password == user['password']):
                self.set_cookie('user', username)
                self.redirect('/')
            else:
                self.redirect('/login')

class BookHandler(BaseHandler):
    
    def get(self, book_id):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = rsdb.getRecbooks(name)
        else:
            rb = None
            name = None

        ret = rsdb.findOneBook(book_id).copy()
        ret['origin_title'] = ret['origin_title'].strip()
        ret['summary'] = rsdb.prettifyText(ret['summary'])
        ret['author_intro'] = rsdb.prettifyText(ret['author_intro'])
        ret['catalog'] = rsdb.prettifyText(ret['catalog'])
        uinfo = rsdb.findOneUser(name)
        if uinfo and 'history' in uinfo:
            rd = [x['book_id'] for x in uinfo['history']]
        else:
            rd = None
        return self.render("book.html", username=name, recbooks=rb, read=rd,
            book_info=rsdb.summaryBook(ret, ti_s=100, au_s=100, ta_s=100, su_s=-1))

    def post(self, book_id):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = rsdb.getRecbooks(name)
        else:
            rb = None
            name = ''
        comment = self.get_argument('comment') 
        rsdb.insertComment(comment, name, book_id)

        ret = rsdb.findOneBook(book_id, update=True).copy()
        ret['origin_title'] = ret['origin_title'].strip()
        ret['summary'] = rsdb.prettifyText(ret['summary'])
        ret['author_intro'] = rsdb.prettifyText(ret['author_intro'])
        ret['catalog'] = rsdb.prettifyText(ret['catalog'])   
        return self.render("book.html", username=name, recbooks=rb,
            book_info=rsdb.summaryBook(ret, au_s=14, ta_s=34, su_s=-1))

class UserHandler(BaseHandler):
    
    def get(self):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = rsdb.getRecbooks(name)
        else:
            rb
            name = None
        user = rsdb.findOneUser(name)
        for h in user['history'][:45]:
            if 'book_id' not in h:
                continue
            book = rsdb.findOneBook(h['book_id']).copy()
            h['book'] = rsdb.summaryBook(book)
        self.render('user.html', username = name, recbooks=rb, userinfo=user)

    def post(self):
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
        else:
            name = None
        book_id = self.get_argument('book_id')
        rate    = self.get_argument('rate')
        try:
            comment = self.get_argument('comment')
            tags    = self.get_argument('tags')
        except:
            comment = None
            tags    = None
        if name:
            history_doc = {'comment':'', 'user_id':name, 'book_id':book_id, 'rate':rate, 'date':datetime.datetime.utcnow()}
            if comment:
                history_doc['comment'] = comment
                rsdb.insertComment(comment, name, book_id)
            if tags and tags != 'null':
                history_doc['tags'] = tags.split(' ')
            ret = db.users.find_one({"user_id":name})
            if 'crawled' not in ret:
                db.users.update({"user_id":name}, {"$push":{"history":history_doc}})
                print "user %s insert one history" % name
        self.redirect('/book/%d' % int(book_id))


class TagHandler(BaseHandler):

    def get(self, tagname):
        if tagname:
            tagname = tagname.decode('utf-8')
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = rsdb.getRecbooks(name)
        else:
            name = None
            rb = None
        tbooks = rsdb.findTagBooks(tagname)[:45]
        return self.render('tag.html', tagname=tagname, username=name, tagbooks=tbooks, recbooks=rb)

    def post(self):
        tagname = self.get_argument('tagname')
        cook = self.get_cookie('user')
        if cook:
            name = tornado.escape.xhtml_escape(cook)
            rb = rsdb.getRecbooks(name)
        else:
            name = None
            rb = None

        tbooks = rsdb.findTagBooks(tagname)[:45]
        return self.render('tag.html', tagname=tagname, username=name, tagbooks=tbooks, recbooks=rb)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')

class RegisterHandler(BaseHandler):
    
    def get(self):
        cook = self.get_cookie('user')
        if cook:
            self.clear_cookie('user')
        name = None        
        self.render('register.html', username=name)

    def post(self):
        name = self.get_argument('username')
        password = self.get_argument('password')
        rsdb.insertUser(name, password)
        self.set_cookie('user', name)
        self.redirect('/')

# mongo数据库配置
conn = MongoClient('localhost',27017) 
db = conn.group_mems
rsdb = RecsysDatabase()
model = AppModel()

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