
#coding:utf-8
from book_recsys import *


if __name__ == '__main__':
    limit = 30
    popbooks = []
    for i,pb in enumerate( db.popbooks.find(limit=61) ):
        if 'author' not in pb:
            continue
        pb['author'] = ','.join(pb['author'])
        if i%2 != 0:
            popbooks.append({'up':pb, 'down':{}})
        else:
            popbooks[len(popbooks)-1]['down'] = pb
    print len([x['down']['title'] for x in popbooks])