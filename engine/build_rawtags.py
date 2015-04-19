# -*- coding: utf-8 -*- 
from book_recsys import *


# param could be a list of list like [[],[],[]] which contains string.
# param could be a list of string.
# return is False or the match value(could be a list or string)
def getCommonValue(values):
    if not values or len(values) == 1 :
        return False

    val = values[0]
    if isinstance(val, list):
        ret = []
        for v in val:
            for value in values:
                if v not in value:
                    break
            else:
                ret.append(v)
        return ret
    elif isinstance(val, str) or isinstance(val, unicode):
        for value in values:
            if val != value:
                return False
        return val

def build_starttags(used_limit):
    rawtags = []
    for t in db.tags.find():
        rawtags.append(t)
    
    rawtags.sort(cmp=lambda x,y: cmp(len(x['book_ref']), len(y['book_ref'])), reverse=True)
    newtags = [x for x in rawtags if len(x['book_ref']) > int(used_limit)]
    rawtags = dict( [(i['name'], i) for i in newtags] )
    prog_d('rawtags len:%d ' % len(rawtags))
    # tag_authors = {tag name: {'author': {book id: [author] }, 'title': {book id: "title"} } }
    tag_metas = dict()
    for book in db.books.find():
        if 'tags' not in book or not book['tags']:
            continue
        for tag in book['tags']:
            if tag['name'] not in tag_metas:
                tag_metas[tag['name']] = dict()
                tag_metas[tag['name']]['author'] = dict()
            if book['author']: # book that have no author will be ignored.
                tag_metas[tag['name']]['author'][book['id']] = book['author'] # a list
    logging.info("finished constructing {tag name: {'author': {book id: [author] }, 'title': {book id: 'title'} } } from db.books")

    # string match
    author = set()
    for b in db.books.find():
        if 'author' in b:
            for a in b['author']:
                author.add(a)
    logging.info("finished query all author from db.books")    

    author_tags = {}
    for t in tag_metas.items():
        if t[0] in rawtags: ####
            if t[0] in author: 
                author_tags[t[0]] = [t[0]]
            if len(t[1]['author']) > 0:
                tagged_author = [x for x in t[1]['author'].values()]
                # should be cases.
                out = getCommonValue( tagged_author ) ####
                if out: 
                    if t[0] not in author_tags:
                        author_tags[t[0]] = out
                    else:
                        author_tags[t[0]] += out

    starttags = list( set(rawtags) - set(author_tags.keys()) )

    # mtrx = solveWord2VecMatrix(starttags)
    # pickle.dump(mtrx, open('dump/Word2VecMtrx.dmp', 'w'))

    with open('log/tags.start-jieba.txt', 'w') as f:
        for m in starttags:
            pstr = '%s 1\n' % m
            f.write(pstr.encode('utf-8'))

    with open('log/tags.start.txt', 'w') as f:
        for m in starttags:
            pstr = '%s\n' % m
            f.write(pstr.encode('utf-8'))
    
    # logging.debug('rawtags: %d, author: %d, starttags: %d' 
    #     % ( len(rawtags), len(author_tags), len(standard_tags) ) )


if __name__ == '__main__':
    logging.info("running %s" % ' '.join(sys.argv))
 
    # check and process input arguments
    if len(sys.argv) < 2:
        print 'usage: python build_starttags.py <used_limit>'
        sys.exit(1)
    used_limit = sys.argv[1]
    build_starttags(used_limit)