# -*- coding: utf-8 -*- 
from book_recsys import *


def main():
    meta = []
    total = db.books.count()
    for i,b in enumerate(db.books.find()):
        if 'title' not in b:
            continue
        if b['title'].strip():
            meta.append(b['title'].strip())
        # if b['subtitle'].strip() and b['subtitle'].find(' ') < 0:
        #     meta.append(b['subtitle'].strip())
        prog_d('append meta.', i, total)

    with open('log/meta.start-jieba.txt' ,'w') as f:
        for m in meta:
            pstr = '%s 1\n' % m
            if pstr.count(' ') == 1:
                f.write(pstr.encode('utf-8'))

if __name__ == '__main__':
    main()