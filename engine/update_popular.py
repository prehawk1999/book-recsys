# -*- coding: utf-8 -*- 
from book_recsys import *

def getSimBooks(book):
    return [{'sim_book_id':book['id'], 'sim_book':book, 'similarity':1}]

def updPopBooks():
    new_hash = getUmodelHash()
    print new_hash
    record = db.popbooks.find_one()
    if record:
        if new_hash == record['update_hash']:
            logging.info('popbooks is up to date.')
            return
        record['update_hash'] = new_hash
        db.popbooks.update({"_id", record['_id']}, record, upsert=True)
    else:
        record = {}
        record['update_hash'] = new_hash
        db.popbooks.insert(record)
    # return
    bid = set()
    books = []
    for u in db.umodel.find():
        user = rsdb.findOneUser(u['user_id'])
        for h in user['history']:
            book = rsdb.findOneBook(h['book_id'])
            if not book:
                continue
            if 'tags' in book and book['tags']:
                if book['id'] not in bid:
                    del book['_id']
                    books.append(book)
                    bid.add(book['id'])

    books.sort(cmp=lambda a,b:cmp(a['tags'][0]['count'], b['tags'][0]['count']), reverse=True)
    # db.popbooks.update(books)

    domain_popbooks = dict([ (x, []) for x in BOOK_DOMAIN ])
    for b in books:
        db.popbooks.update({"book_id":b['id']}, b, upsert=True)
        if b['general_domain']:
            dom = b['general_domain'][0][0]
            if len(domain_popbooks[dom]) < 20:
                domain_popbooks[dom].append(b)

    db.dombooks.insert(domain_popbooks)


def getUmodelHash():
    hashstr = ''
    hashlst = []
    for u in db.umodel.find():
        hashlst.append(str(u['uptime']))
    return hash( str(hashlst.sort()) )

def main():
    updPopBooks()

if __name__ == '__main__':
    main()
    # getUmodelHash()