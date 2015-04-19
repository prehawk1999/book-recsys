#coding=utf-8
import web
import time

urls = (
    '/', 'index',
    '/xml', 'pushxml',
    '/login', 'login',
    '/logout', 'logout',
)
render = web.template.render('templates/')
web.config.debug = False
app = web.application(urls, locals())
session = web.session.Session(app, web.session.DiskStore('sessions'))      

class index():
    def GET(self):
        try:
            if session.logged_in == True:
                return '<h1>You are logged in</h1><a href="/logout">Logout</a>'
        except AttributeError:
            pass
        return '<h1>You are not logged in.</h1><a href="/login">Login now</a>'

def authorize(func):
    def logged(*args,**dic):
        if session.logged_in==True:
            func(*args,**dic)
        else:
            raise web.seeother('/login')
    return logged

class pushxml():
    # @authorize
    def GET(self):
        try:
            if session.logged_in == True:
                web.header('Content-Type', 'text/xml')
                i = web.input(data=None)
                return render.response(i.data)
        except AttributeError:
            pass
       
class login():
    def GET(self):
        try:
            session.logged_in = False
        except AttributeError:
            pass
        return """
            <form action=/login method=POST>
                <table id="login">
                    <tr>
                        <td>User: </td>
                        <td><input type=text name='user'></td>
                    </tr>
                    <tr>
                        <td>Password: </td>
                        <td><input type="password" name=passwd></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td><input type=submit value=LOGIN></td>
                    </tr>
                </table>
            </form>
        """
           
    def POST(self):
        login_data = web.input()
        if login_data.user == 'a' and login_data.passwd == 'a':
            session.logged_in = True
            print "posted"
            print session
            raise web.seeother('/')
       
class logout():
    def GET(self):
        try:
            session.logged_in = False
            session.kill()
        except AttributeError:
            pass
        raise web.seeother('/')

if __name__ == '__main__':
    app.run()