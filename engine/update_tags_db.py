# -*- coding: utf-8 -*- 
from book_recsys import *


def update_tags_db():
    global PROG

    tags_summary = {}
    book_total_f = {}
    tags_totalcount = 0

    ### 提取用户表中的每本书的标签数量和总数量
    for i, user in enumerate(db.users.find()):
        if 'history' not in user or len(user['history']) < 15:
            continue
        for h in user['history']:
            if h['book_id'] not in book_total_f:
                book_total_f[h['book_id']] = 0.0
            if 'tags' in h:
                book_total_f[h['book_id']] += len(h['tags'])
                tags_totalcount += len(h['tags'])
    prog_d('extract tags in users ')
    
    ### 所有书籍的所有标签
    for book in db.books.find():
        if 'tags' not in book or not book['tags']:
            continue
        for t in book['tags']:
            tags_totalcount += t['count']
    prog_d('extract tags in books')


    ### 汇总标签数据结构
    # PROG = db.books.count()
    for i, book in enumerate(db.books.find()):
        if 'tags' not in book or not book['tags']:
            continue
        book_tags = book['tags']

        # 计算书籍的所有标签的标注次数之和，包括用户标注的标签
        total_tcount = 0
        for tag in book_tags:
            total_tcount += tag['count']
        if book['id'] in book_total_f:
            total_tcount += book_total_f[book['id']]

        for j, tag in enumerate(book_tags):
            # score = float(tag['count'] + 1) / float(prime_tag_count + 1)
            if tag['name'] not in tags_summary:
                tags_summary[tag['name']] = {'count': 0, 'book_ref':list()}

            tf = float(tag['count']) / float(total_tcount)
            tags_summary[tag['name']]['book_ref'].append( (book['id'], j, float(tag['count']), tf) )
            tags_summary[tag['name']]['count'] += tag['count']

    ### 计算每个标签的idf
    for i, key in enumerate(tags_summary.keys()):
        tags_summary[key]['idf'] = math.log( float(tags_totalcount) / float(tags_summary[key]['count'] + 1) )
    prog_d('prepare data structure')

    ### 汇集用户引用
    for i, u in enumerate(db.users.find()):
        if 'history' not in u or len(u['history']) < 15:
            continue
        for h in u['history']:
            if 'tags' not in h:
                continue
            for t in h['tags']:
                if t in tags_summary:
                    if 'user_ref' not in tags_summary[t]:
                        tags_summary[t]['user_ref'] = set()
                    tags_summary[t]['user_ref'].add(u['user_id'])
    
    for i, tag in enumerate(tags_summary.items()):
        if 'user_ref' in tag[1]:
            tags_summary[tag[0]]['user_ref'] = list(tag[1]['user_ref'])

    prog_d('add user ref to tags.')

    # 把整理后的tags_summary存进数据库里
    PROG = len(tags_summary)
    for i, t in enumerate(tags_summary.items()):
        document = db.tags.find_one({"name":t[0]})
        if not document:
            document = {"name":t[0]}
        document.update(t[1])
        db.tags.update({"name":t[0]}, document, upsert=True)
        prog_d('update or insert mongo', i, PROG)
    prog_d('updateRawtags')

if __name__ == '__main__':
    update_tags_db()