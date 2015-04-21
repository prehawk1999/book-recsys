#coding=utf-8
from model import *
import web
from web import form

urls = (
    '/', 'Index',
    '/book/(\d+)', 'Book', 
    '/user/(\d+)', 'User',
    '/tag/(\d+)', 'Tag', 
    '/login', 'Login',
    '/logout', 'Logout',
    '/register', 'Register',
)

#模板公共变量
t_globals = {
    'datestr': web.datestr,
    'cookie': web.cookies,
}

app = web.application(urls, locals())
render = web.template.render('templates/')
session = web.session.Session(app, web.session.DiskStore('sessions'))  
web.config.debug = False


login = form.Form(
            form.Textbox('username'),
            form.Password('password'),
            form.Button('login')
    )
  
register = form.Form(
            form.Textbox('username', form.regexp(r".{3,20}$", '用户名长度为3-20位'), description=u'用户名'), 
            form.Textbox('email', form.regexp(r".*@.*", "must be a valid email address") , description=u'电子邮箱') 
            form.Password("password", form.regexp(r".{6,20}$", '密码长度为6-20位'), description=u"密码"),  
            form.Password("password2", description=u"确认密码"),  
            form.Button("register", type="submit", description="submit"),  
            form.Textbox('idcode')
            validators = [ form.Validator("两次输入的密码不一致", lambda i: i.password == i.password2) ]
    )  

class Index(object):
    def GET(self, name='prehawk'):
        return render.index(name, popbooks, recbooks)
    def POST(self):
        pass

class Login(object):
    def POST(self):
        f = form
        print '%r' % f

class Book(object):
    def GET(self, book_id):
        # return '<p>%s</p>' % book_id
        book_info = rsdb.findOneBook(book_id)
        return render.book(book_info)

class User(object):
    pass

class Tag(object):
    pass

class Logout(object):
    pass

class Register(object):
    pass

if __name__ == '__main__':
    app.run()