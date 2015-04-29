# -*- coding: utf-8 -*- 
from book_recsys import *
from stdtag import StandardTags
from FieldTree import *

stdtag._loadStart()

## 用户标注标签对兴趣模型的权重
USER_TAG_W = 2

##书籍原有标签对兴趣模型的权重
BOOK_TAG_W = 1

## 书籍推荐评分数量限制
BOOK_REC_NUM = 50

## 根据兴趣模型的书籍得分推荐阀值
BOOK_INT_THRES = 20

# 一些需要用到的全局数据
G_umodels   = {}
G_historys = {}

### 用户模型表umodel
#   通过阅读历史计算的模型增量
#   用户模型更新时间updatetime: 
def updateUserModel(user, nowtime, utype):
    count = 0

    # user表中的记录表和umodel表中的长度不同则优先计算user表中剩下的history
    # 否则如果更新时间有差异更新所有umodel中的条目
    #判断umodel表的数据是否是最新的（根据user表）
    umodel = db.umodel.find_one({"user_id":user['user_id']})
    if not umodel:
        umodel = {'history_vec':[], 'uptime':nowtime, 'user_id':user['user_id'], 'type':utype}
        u_id = db.umodel.insert(umodel)
        logging.info('create user %s model _id %s' % (user['user_id'], u_id) )
    else:
        if len(umodel['history_vec']) != len(user['history']):
            count = len(umodel['history_vec'])
        elif (nowtime - umodel['uptime']).days == 0:
            logging.info('- user %s model is up to date.' % umodel['user_id']) # 通过user表来更新umodel表
            return umodel

    # 遍历用户阅读历史
    for h in user['history'][count:]:
        #得到一条阅读历史的兴趣向量(字典)
        tag_vec, book_vec = getVecByHistory(h)
        history_vec  = {"date" : h['date'], "book_id": h['book_id'], "tag_vec" : tag_vec, "book_vec" : book_vec}
        umodel['history_vec'].append(history_vec)
    u_id = umodel['_id']
        
    umodel['interest_eval'] = {}
    #user_fields:初始化一个用户的专业树
    user_fields = FieldTree(FIELDS)
    for h in umodel['history_vec']:
        # 累加最终兴趣向量
        #items将字典转化为列表
        for t in h['book_vec'].items():
            #t[0]系文本；t[1]系权重
            if t[0] not in umodel['interest_eval']:
                umodel['interest_eval'][t[0]] = 0.0
            #umodel['interest_eval']系用户最终向量的字典；[t[0]]取出t[0]键所对应的值；
            #书籍标签权重要乘上时间系数
            umodel['interest_eval'][t[0]] += getEbbinghausVal(nowtime, h['date']) * t[1]
        for t in h['tag_vec'].items():
            if t[0] not in umodel['interest_eval']:
                umodel['interest_eval'][t[0]] = 0.0
            #用户自定义标签不需要乘上时间系数
            umodel['interest_eval'][t[0]] += t[1]

        #专业向量
        # 获得历史记录的书籍
        book = rsdb.findOneBook(h['book_id'])
        if not book or 'tags' not in book:
            continue
        user_fields.insertBook( book )
        #将每条历史的兴趣向量存入数据库的umodel表
        db.umodel.update({"_id":u_id}, {"$addToSet":{"history_vec":history_vec}})
        # logging.info('-=-=-=INSERT-=-=-=- history_vec interest %s, pro %s, on date %s' % (' '.join([unicode(x[0])+unicode(x[1]) for x in interest_vec.items()]), ' '.join([unicode(x[0])+unicode(x[1]) for x in pro_vec.items()]), h['date']) )
    
    #获得最终的专业向量
    umodel['field_eval'] = user_fields.getVector()
    #记录更新时间
    umodel['uptime'] = nowtime
    db.umodel.update({'_id':u_id}, umodel, upsert=True)
    logging.info('-=-=-=- evaluate -=-=-=- final vector: ||interest|| %s, ||pro|| %s' 
        % (' '.join([unicode(x[0])+unicode(x[1]) for x in umodel['interest_eval'].items()]), ' '.join( [unicode(x[0])+unicode(x[1]) for x in umodel['field_eval'].items()] )) )
    return umodel

### 根据每条历史获得兴趣向量
def getVecByHistory(history):

    # 兴趣向量，用用户的标签标示
    tag_vec = {}
    book_vec = {}

    # 根据用户显式标注的标签（用户自己写的标签）来累加兴趣向量，但是对专业向量没有影响

    if 'tag' in history:
        for usertag in history['tags']:
            #标签标准化 ：利用互信息将使用次数较少的标签聚类到使用次数较多的标签上
            realtag = stdtag.simple_transform(usertag)
            #mongodb不支持小数点，tag里面不能有小数点
            if realtag and realtag.find('.') == -1:

                # 获得标签的idf
                #找数据库中标签的idf，有的话就是tag_idf，没有的话就是1
                ret = rsdb.findOneTag(realtag)
                if ret:
                    tag_idf = ret['idf']
                else:
                    tag_idf = 1
                    logging.warn('tag %s get idf error.' % realtag)

                if realtag not in tag_vec:
                    tag_vec[realtag] = 0
                #USER_TAG_W是用户自定义标签的权重，经验值，需考察；
                #计算兴趣向量中标签的权重（叠加）
                tag_vec[realtag] += USER_TAG_W * tag_idf

    # 根据书籍所拥有的8个标签来累加兴趣向量
    book = rsdb.findOneBook(history['book_id'])
    if book:
        #遍历书中的每个热门标签
        for booktag in [x['name'] for x in book['tags']]:
            realtag = stdtag.simple_transform(booktag)
            if realtag and realtag.find('.') == -1:

                # 获得标签的idf
                ret = rsdb.findOneTag(realtag)
                if ret:
                    tag_idf = ret['idf']
                else:
                    tag_idf = 1
                    logging.warn('tag %s get idf error.' % realtag)

                if realtag not in book_vec:
                    book_vec[realtag] = 0
                book_vec[realtag] += BOOK_TAG_W * tag_idf

    return tag_vec, book_vec

### 根据艾宾浩斯遗忘公式，计算两个日子间隔表示的时间系数
def getEbbinghausVal(nowtime, history_date, c=1.25, k=1.84):
    timediff = nowtime - datetime.datetime.strptime(history_date, "%Y-%m-%d")
    return float(k)/float(math.log(timediff.days)**c+k)

### 根据users表更新umodels表的每个用户,以及缓存部分数据
#   给每个用户生成 books, users, umodel, tags
def generateUModelFromUsers(query):
    total = db.users.find(query).count()
    for u in db.users.find(query, timeout=False):
        #updateUserModel函数是计算特定用户的模型；
        #u是用户；第二个参数是当前时间
        um = updateUserModel(u, datetime.datetime(2015,4,1), 'recsys')
        G_umodels[u['user_id']] = um
        G_historys[u['user_id']] = u['history']   
        rsdb.cacheUsers(u)

### 根据interest_eval生成interest_recbooks, 根据FieldTree里的每个标签的已排名书目生成field_recbooks
def generateRecBooksFromUModel():
    ### 开始整理umodels表里用户的信息
    #i:索引；u：umodel表中每个用户模型；enumerate：计数器
    for i,u in enumerate(G_umodels.values()):

        # 用户已阅读书籍
        user_read = [ x['book_id'] for x in G_historys[u['user_id']] ]
        # logging.info('user_read:%r' % user_read )

        ## 获得根据用户兴趣向量的推荐书籍, 需要排除已阅读书籍
        if 'interest_eval' in u:
            user_books = []
            #计算数据库中的所有书籍的兴趣得分
            for book in rsdb.findBooks():
                if not book or 'tags' not in book:
                    continue
                weight = 0.0
                #对于书中的所有热门标签进行与兴趣向量的匹配，如果在兴趣向量中存在这个标签，则书籍得分
                #会加上这个标签的权重
                for t in book['tags']:
                    if t['name'] in u['interest_eval'].keys():
                        weight += u['interest_eval'][t['name']]
                if book['id'] not in user_read:
                    # if weight > BOOK_INT_THRES:
                    user_books.append( (book['id'], weight, book['title']) )
            user_books.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
            u['interest_recbooks'] = user_books[:BOOK_REC_NUM]
            if len(user_books) > 0:
                logging.info('sort interest_recbooks for user %s len:%d' % (u['user_id'], len(user_books)) )

        ## 获得根据用户专业向量的推荐书籍
        # 专业向量中每个分量所代表的节点的书籍去除该用户阅读过的书籍
        if 'field_eval' in u:
            u['field_recbooks'] = {}
            for uf in u['field_eval'].items():
                user_books = []
                for node in FieldTree.field_nodes:
                    if not node.match(uf[0]):
                        continue
                    for book in node.books:
                        if book not in user_read:
                            user_books.append( (book['id'], book['title']) )
                            if len(user_books) > BOOK_REC_NUM:
                                break
                u['field_recbooks'][uf[0]] = user_books
            # u['field_recbooks'] = user_books
            if len(user_books) > 0:
                logging.info('sort field_recbooks for user %s len:%d' % (u['user_id'], len(user_books)) )



        ## 写入用户最终推荐书目
        ret = db.umodel.update({"_id":u['_id']}, u)
        # logging.info('update user recommend books %s' % u['user_id'] )

def sortFieldNodeTree():
    ## 对每个节点标签进行书籍的排序
    #idx：表示节点列表中这本书属于第几个；fn：节点；节点是列表
    for idx,fn in enumerate(FieldTree.field_nodes):

        # 比较函数：按照专业度来排序（用户）；若a & b的专业度相同的话，就按照用户创建时间来排
        def umodel_sort(a, b):
            aval = a['field_eval'][fn.name]
            bval = b['field_eval'][fn.name]
            if aval > bval:
                return 1
            elif aval == bval:
                adate = datetime.datetime.strptime(a['history_vec'][0]['date'], "%Y-%m-%d")
                bdate = datetime.datetime.strptime(b['history_vec'][0]['date'], "%Y-%m-%d")
                daydiff = (adate - bdate).days
                if daydiff > 0:
                    return 1
                else:
                    return -1
            else:
                return -1
 
        # 首先根据这个节点标签, 按照field_eval[fn.name]对所有用户进行排序, 从小到大
        # 然后根据用户的建立时间排序，也是从小到大
        # fliter有专业向量嘅用户；
        umodels = [ x for x in G_umodels.values() if 'field_eval' in x and fn.name in x['field_eval'] ]
        #根据just嘅比较函数来排序
        umodels.sort(cmp=umodel_sort, reverse=False)
        logging.debug('=%s=SORTING field_nodes:%s, len of umodels:%d, ' % ('-'*1, fn.name, len(umodels)) )
        
        #um：每个用户模型中的用户
        for um in umodels: # 对于每个用户
            #raw_books: 啱先果啲排好序嘅用户嘅阅读历史
            raw_books = [ rsdb.findOneBook(x['book_id']) for x in G_historys[um['user_id']] if rsdb.findOneBook(x['book_id']) ]
            raw_books.sort(cmp=lambda a,b:cmp(a['rating']['average'], b['rating']['average']), reverse=True)
            #将书插入当前遍历节点
            for b in raw_books:
                ret = FieldTree.field_nodes[idx].insertBook(b)
                if ret:
                    logging.debug('=%s=INSERT book %s' % ('-'*9, b['title']) )

    # 输出每个节点的 书籍情况
    for fn in FieldTree.field_nodes:
        logging.info('node:%s, %d books inserted.' % (fn.name, len(fn.books)) )


def main():
    # FieldTree.field_nodes = pickle.load(open('dump/FieldNodes'))
    #对阅读量大于15小于60的用户进行模型计算；将user表中的数据计算后保存到umodel表
    generateUModelFromUsers({'read':{'$gte':15, '$lte':60}})
    #保存最新更新的专业树
    pickle.dump(FieldTree.field_nodes, open('dump/FieldNodes', 'w'))

    sortFieldNodeTree()
    generateRecBooksFromUModel()

if __name__ == '__main__':
    main()
    
