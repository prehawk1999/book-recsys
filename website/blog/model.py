#coding:utf-8
import web
import datetime
#数据库连接
db = web.database(dbn = 'mysql', db = 'test', user = 'root', pw = '123456')
#获取所有文章
def get_posts():
    return db.select('entries', order = 'id DESC')
    
#获取文章内容
def get_post(id):
    try:
        return db.select('entries', where = 'id=$id', vars = locals())[0]
    except IndexError:
        return None
#新建文章
def new_post(title, text):
    db.insert('entries',
        title = title,
        content = text,
        posted_on = datetime.datetime.utcnow())
#删除文章
def del_post(id):
    db.delete('entries', where = 'id = $id', vars = locals())
    
#修改文章
def update_post(id, title, text):
    db.update('entries',
        where = 'id = $id',
        vars = locals(),
        title = title,
        content = text)