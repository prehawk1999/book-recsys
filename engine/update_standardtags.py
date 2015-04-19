# -*- coding: utf-8 -*- 
from book_recsys import *
from stdtag import StandardTags

### 更新tags表，每个标签都对应有一个相似标签列表，但是如果本身是启动标签或者没有相似标签的话便是[]
def update_standard_tags():
    stdtag = StandardTags()
    total = db.tags.find().count()
    logging.debug('remaining %d tags without standard.' % total)
    for i,t in enumerate( db.tags.find(timeout=False) ): # {"$where":"this.standard == null"}, timeout=False
        taglst = stdtag.transform(t['name'])
        if not taglst or taglst[0][0] == t['name']:
            logging.debug('skip tag: %s', t['name'])
            t['standard'] = []
        else:
            t['standard'] = taglst
            logging.debug( '%d, tag update standard %s --> %s' % (i, t['name'], taglst[0][0]) )
        ret = db.tags.update({"_id":t['_id']}, t)
        if not ret['ok']:
            logging.warn('tag update failed. tag: %s' % t['name'])
        prog_d('tag update', i, total)


if __name__ == '__main__':
    update_standard_tags()