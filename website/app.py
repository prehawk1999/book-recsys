#coding=utf-8
import tornado.ioloop
import tornado.web
from book_recsys import *


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        
        limit = 30
        popbooks = []
        recbooks = []
        for i,pb in enumerate( db.popbooks.find(limit=61) ):
            if 'author' not in pb:
                continue
            pb['author'] = ','.join(pb['author'])
            if len(pb['summary']) > 24:
                pb['summary'] = pb['summary'][:24] + '......'
            pb['tags'] = '/'.join([ x['name'] for x in pb['tags'] ])
            if len(pb['tags']) > 12:
                pb['tags'] = pb['tags'][:12] + '......'

            recbooks.append(pb)
            if i%2 != 0:
                popbooks.append({'up':pb, 'down':{}})
            else:
                popbooks[len(popbooks)-1]['down'] = pb
        self.render("index.html", username=name, popbooks=popbooks, recbooks=recbooks)

class LoginHandler(BaseHandler):
    def get(self):
        self.render('/login.html')
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
    pass
    # def get(self, book_id):
    #     # return '<p>%s</p>' % book_id
    #     book_info = rsdb.findOneBook(book_id)
    #     return render.book(book_info)

class UserHandler(BaseHandler):
    pass

class TagHandler(BaseHandler):

    def get(self):
        pass

    def post(self):
        # self.write(self.get_argument())
        pass


class LogoutHandler(BaseHandler):
    pass

class RegisterHandler(BaseHandler):
    pass

settings = {
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__", # 安全cookie所需的
    "login_url": "/login", # 默认的登陆页面，必须有
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_url_prefix": "/templates/"
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