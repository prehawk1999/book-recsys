# -*- coding: utf-8 -*- 
from book_recsys import *
import gensim


class count_dict(dict):
    def __missing__(self, key):
        return 0


def test_mark_sample():
    books_sample = []
    with open('mark.sample.txt') as f:
        spamreader = csv.reader(f)
        #print spamreader
        for row in spamreader:
            #print int(row[len(row)-1].strip())
            books_sample.append( (row[0].strip().decode('utf-8'), int(row[len(row)-1].strip()) ) )

    tags = getRawTags(used_limit=10)
    
    for b in books_sample: # id, pro
        onebook = db.books.find_one({"id":b[0]})
        if 'tags' not in onebook:
            continue
        for i,tag in enumerate(onebook['tags']):
            #print tag_name, type(tag_name)
            tag_name = tag['name']
            if b[1] == 1 and tag_name in tags:
                if 'score' not in tags[tag_name]:
                    tags[tag_name]['score'] = 0
                tags[tag_name]['score'] += 8 - i
        logging.debug('book %s in books_sample' % b[0] )

    tags_display = [x for x in tags.values() if 'score' in x]
    #print tags_display[1]
    tags_display.sort( cmp=lambda a,b: cmp(float(a['score'])/float(tags[a['name']]['count']), float(b['score'])/float(tags[b['name']]['count'])), reverse=True ) 
    

    # 计算标签的专业度
    with open('mark.rank.txt', 'w') as f:
        for t in tags_display:
            wstr = '%s, %f\r\n' % ( t['name'], float(t['score'])/float(tags[t['name']]['count']) )
            f.write(wstr.encode('utf-8'))
            print wstr

    logging.info('finished test_mark_sample')

def test_book_prof():
    #books = getSomeBooks(0, False)
    tags_pro = {}
    with open('mark.rank.txt') as f:
        reader = csv.reader(f)
        tags_pro = dict([( row[0].decode('utf-8'), float(row[1]) ) for row in reader])

    #book_sample = []
    book_ranked = []
    with open('books.sample0.txt') as f:
        reader = csv.reader(f)
        for row in reader:
            book = db.books.find_one({"id":row[0].decode('utf-8')})
            if book and 'tags' in book:
                score = 0
                for t in book['tags']:
                    if t['name'] in tags_pro:
                        score += tags_pro[t['name']]
                #wstr = '%s, %f' % (book['title'], score)
                book_ranked.append( (book['title'], score) )

    book_ranked.sort( cmp=lambda a,b: cmp(a[1], b[1]), reverse=True )
    for b in book_ranked:
        print '%s, %f' % (b[0], b[1])
        #book_sample = [row[0].decode('utf-8') for row in reader]
    
def test_user_pro():

    tags_pro = {}
    with open('mark.rank.txt') as f:
        reader = csv.reader(f)
        tags_pro = dict([( row[0].decode('utf-8'), float(row[1]) ) for row in reader])

    tags = getRawTags(pdebug=True)
    tags_acc = count_dict()
    for u in db.users.find():
        if 'history' in u:
            for h in u['history']:
                if 'tags' in h:
                    for t in h['tags']:
                        tags_acc[t] += 1

    ret = set(tags_acc.keys()) - set(tags.keys())
    for r in ret:
        print r
    #print len(tags), len(tags_acc)
  
def test_user_model():
    tags_cluster = pickle.load(open('tgcl.dmp'))
    # for i in cluster.items():
    #     print i[0], ' '.join(i[1])

    tags_pro = dict([ (row[0].decode('utf-8'), float(row[1])) for row in csv.reader(open('mark.rank.txt'))])
               
    invert_tags = {}
    for i in tags_cluster.items():
        for j in i[1]:
            if i[0] in tags_pro:
                invert_tags[i[0]] = (j, tags_pro[i[0]])
            else:
                invert_tags[i[0]] = (j, 0.0)

    dearcloud = db.users.find_one({"user_id":"cugbnxx"})
    dearcloud_vec = dict( [(x, 0.0) for x in tags_cluster.keys()] )

    # 所有历史累加
    for h in dearcloud['history']:
        book = db.books.find_one({"id":h['book_id']})
        if book and 'title' in book:
            if 'tags' in book:
                for t in book['tags']:
                    if t['name'] in dearcloud_vec:
                        dearcloud_vec[t['name']] += 0.1

        if 'tags' not in h:
            continue

        for t in h['tags']:
            if t not in dearcloud_vec:
                continue
            dearcloud_vec[t] += 1

    dvs = dearcloud_vec.items()
    dvs.sort(cmp=lambda a,b: cmp(a[1],b[1]), reverse=True)
    for i in dvs:
        print i[0], i[1]


# get raw tags from db.tags
def getRawTags(count_limit=-1, score_limit=-1, used_limit=-1, pdebug=False):

    ret = []
    for t in db.tags.find():
        ret.append(t)
    if score_limit >= 0:
        ret.sort(cmp=lambda x,y: cmp(x['count'], y['count']), reverse=True)
        ret = [x for x in ret if x['count'] > score_limit]
    if used_limit >= 0:
        ret.sort(cmp=lambda x,y: cmp(len(x['book_ref']), len(y['book_ref'])), reverse=True)
        ret = [x for x in ret if len(x['book_ref']) > used_limit]
    if count_limit >= 0:
        ret = ret[:count_limit]

    if pdebug:
        c = 0 
        with open('tags.record%d.txt' % used_limit, 'w') as f:
            for i in ret:
                #print i
                if len(i['book_ref']) > 0: 
                    c += 1
                    pstr = '%s, %f, %d \r\n' % (i['name'], i['count'], len(i['book_ref']))
                    #print pstr
                    f.write(pstr.encode('utf-8'))
            print 'tag count: ', c    
    prog_d('getRawTags')
    return dict([(i['name'], i) for i in ret]) 
 
def getSomeBooks(offset=0, write=True):
    books = []
    for i in db.books.find():
        if 'title' in i:
            books.append(i)
        # print i['id']
    logging.info('finished adding complete books to array')

    books_sample = getSample(books, 100, offset)
    print len(books_sample)

    if write:
        with open('books.sample%d.txt' % offset, 'w') as f:
            for i in books_sample:
                wstr = '%s, %s, %s, %s,  \r\n' % (i['id'], 'http://book.douban.com/subject/%s/' % i['id'],  i['title'], ' '.join([x['name'] for x in i['tags']]) )
                f.write(wstr.encode('utf-8'))
                logging.info('writing book info %s' % i['id'])
    
    return books_sample

def getSample(raw_list, x, offset=0):
    sample = []
    a = len(raw_list)
    for i in range(a/x):
        rotate_index = ( (a % x)*i + offset ) % a
        sample.append(raw_list[rotate_index])
    return sample




def main():
    pass
    
if __name__ == '__main__':
    logging.info('=-=-=-=-=    TAG_ANALYSIS START!!!    =-=-=-=-=-=')
    console.setLevel(logging.DEBUG)
    main()
    logging.info('=-=-=-=-=    TAG_ANALYSIS END!!!    =-=-=-=-=')


