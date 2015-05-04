# -*- coding: utf-8 -*- 
from book_recsys import *
from FieldTree import *

#### 影响推荐效果的几个参数

## 用户标注标签对兴趣模型的权重
USER_TAG_W = 1

##书籍原有标签对兴趣模型的权重
BOOK_TAG_W = 0.5

## 书籍推荐评分数量限制
BOOK_REC_NUM = 20

## 兴趣向量窗口大小
INT_VEC_MAX = 1000

## 相似用户窗口
USER_SIM_WINDOW = 40

## 开启标签标准化
ENABLE_STANDALIZE = True


## 训练集比重
TRAIN_RATIO = 0.8



# 缓存用户阅读历史和用户模型
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

    umodel = {'uptime':nowtime, 'user_id':user['user_id'], 'type':utype}
    u_id = db.umodel.insert(umodel)
    train_idx = int( len(user['history']) * TRAIN_RATIO )
    logging.info('create user %s Training data: ratio: %f, totallen: %d, scope: %d - %d' % (user['user_id'], TRAIN_RATIO, len(user['history']), count, train_idx) )
    
    # 遍历用户阅读历史
    history_vec_list = []
    for i,h in enumerate(user['history'][count:]):
        #得到一条阅读历史的兴趣向量(字典)
        tag_vec, book_vec = getVecByHistory(h)
        if i > train_idx:
            continue
        history_vec  = {"date" : h['date'], "book_id": h['book_id'], "tag_vec" : tag_vec, "book_vec" : book_vec}
        history_vec_list.append(history_vec)
        #将每条历史的兴趣向量存入数据库的umodel表
        # db.umodel.update({"_id":u_id}, {"$addToSet":{"history_vec":history_vec}})
        
    umodel['interest_eval'] = {}
    #user_fields:初始化一个用户的专业树
    user_fields = FieldTree(FIELDS)
    for h in history_vec_list:
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
        # logging.info('-=-=-=INSERT-=-=-=- history_vec interest %s, pro %s, on date %s' % (' '.join([unicode(x[0])+unicode(x[1]) for x in interest_vec.items()]), ' '.join([unicode(x[0])+unicode(x[1]) for x in pro_vec.items()]), h['date']) )
    
    #获得最终的专业向量
    umodel['field_eval'] = user_fields.getVector()
    tmp_eval = umodel['interest_eval'].items()
    tmp_eval.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
    umodel['interest_eval'] = dict(tmp_eval[:INT_VEC_MAX]) # 获得比重最大的INT_VEC_MAX个兴趣向量分量

    #记录更新时间
    umodel['uptime'] = nowtime
    db.umodel.update({'_id':u_id}, umodel, upsert=True)
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
            if ENABLE_STANDALIZE:
                realtag = stdtag.simple_transform(usertag)
            else:
                realtag = usertag

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
            if ENABLE_STANDALIZE:
                realtag = stdtag.simple_transform(booktag)
            else:
                realtag = booktag

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
def generateUModelFromUsers(query, limit):
    db.umodel.remove({})
    total = db.users.find(query, limit=limit).count()
    for i,u in enumerate(db.users.find(query, limit=limit, timeout=False)):
        #updateUserModel函数是计算特定用户的模型；
        #u是用户；第二个参数是当前时间
        um = updateUserModel(u, datetime.datetime(2015,4,1), 'recsys')
        # 缓存用户阅读历史和计算出来的用户模型
        G_umodels[u['user_id']] = um
        G_historys[u['user_id']] = u['history']   
        rsdb.cacheUsers(u)

### 计算用户相似度，利用余弦公式
def getCosSim(a_vec, b_vec):
    RU = 0.0
    Ra = 0.0
    Rb = 0.0
    for k in a_vec.keys():
        if k not in b_vec:
            continue
        RU += a_vec[k]*b_vec[k]
        Ra += a_vec[k]**2
        Rb += b_vec[k]**2 
    RaD = math.sqrt(Ra)
    RbD = math.sqrt(Rb)
    root = RaD * RbD
    if root != 0:
        return RU / RaD * RbD
    else:
        return 0.0

## 获得相似用户所阅读的书籍，相似用户群大小由USER_SIM_WINDOW决定
def getSimUsersBooks(user):
    sis = {}
    # 遍历每个用户模型
    for um in G_umodels.values():
        if user['user_id'] == um['user_id']:
            continue
        # 计算user跟每个用户模型的相似度，并保存到sis字典里
        si = getCosSim(um['interest_eval'], user['interest_eval'])
        sis[um['user_id']] = si

    # 根据相似度进行排序，相似度大的排在前面
    sis_sort = sis.items()
    sis_sort.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)

    # 标记用户书籍
    bids = []
    books = []
    for s in sis_sort[:USER_SIM_WINDOW]:
        bids += [x['book_id'] for x in G_historys[s[0]]]
    for b in set(bids):
        books.append(rsdb.findOneBook(b))
    return books


### 根据interest_eval生成interest_recbooks, 根据FieldTree里的每个标签的已排名书目生成field_recbooks
def generateRecBooksFromUModel():
    ### 开始整理umodels表里用户的信息
    #i:索引；u：umodel表中每个用户模型；enumerate：计数器
    for i,u in enumerate(G_umodels.values()):

        # 用户已阅读书籍，只统计训练集上的已阅读书籍
        train_idx = int( len(rsdb.findOneUser(u['user_id'])['history']) * TRAIN_RATIO )
        user_read = [ x['book_id'] for x in G_historys[u['user_id']][train_idx:] ]

        # 每个领域限定书籍书目
        domain_limit = {}
        ## 获得根据用户兴趣向量的推荐书籍, 需要排除已阅读书籍
        if 'interest_eval' in u:
            user_books = []
            #计算数据库中的所有书籍的兴趣得分

            # 获得邻近用户群所阅读的书籍
            books = getSimUsersBooks(u)
            for book in books:
                if not book or 'tags' not in book:# or book['id'] not in user_unread:
                    continue

                # #对于书中的所有热门标签进行与兴趣向量的匹配，如果在兴趣向量中存在这个标签，则书籍得分
                # #会加上这个标签的权重
                weight = getCosSim(u['interest_eval'], dict([(t['name'], float(8-i)/10) for i,t in enumerate(book['tags'])]) )        
                if weight <= 0.0:
                    continue

                if book['id'] not in user_read:
                    user_books.append( (book['id'], weight, book['title']) )
            user_books.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)      
            u['interest_recbooks'] = user_books[:BOOK_REC_NUM]
            print '\n user %s: interest_eval: %s' % (u['user_id'], ' '.join([unicode(x[0])+unicode(x[1]) for x in G_umodels[u['user_id']]['interest_eval'].items() ]) )
            print '\n check rec books', ' '.join([ rsdb.findOneBook(x[0])['title']+unicode(x[1]) for x in u['interest_recbooks'] ])
            if len(user_books) > 0:
                logging.info('sort interest_recbooks for user %s len:%d' % (u['user_id'], len(user_books)) )

        ## 获得根据用户专业向量的推荐书籍
        # 专业向量中每个分量所代表的节点的书籍去除该用户阅读过的书籍
        # if 'field_eval' in u:
        #     u['field_recbooks'] = {}
        #     for uf in u['field_eval'].items():
        #         user_books = []
        #         for node in FieldTree.field_nodes:
        #             print '-=-'*10, node.name
        #             if not node.match(uf[0]):
        #                 continue
        #             for book in node.books:
        #                 if book not in user_read:
        #                     print book['title']
        #                     user_books.append( (book['id'], book['title']) )
        #                     if len(user_books) > BOOK_REC_NUM:
        #                         break
        #         u['field_recbooks'][uf[0]] = user_books
        #     # u['field_recbooks'] = user_books
        #     if len(user_books) > 0:
        #         logging.info('sort field_recbooks for user %s len:%d' % (u['user_id'], len(user_books)) )



        ## 写入用户最终推荐书目
        ret = db.umodel.update({"_id":u['_id']}, u)
        # logging.info('update user recommend books %s' % u['user_id'] )

def sortFieldNodeTree():
    ## 对每个节点标签进行书籍的排序
    #idx：表示节点列表中这本书属于第几个；fn：节点；节点是列表
    for idx,fn in enumerate(FieldTree.field_nodes):

        books = []
        for bid in FieldTree.field_nodes[idx].books_allow:
            book = rsdb.findOneBook(bid)
            # print '='*20, book['title']
            books.append(book)

        # print len(books)
        books.sort(cmp=lambda a,b:cmp(a['tags'][0]['count'], b['tags'][0]['count']), reverse=True)
        for b in books:
            FieldTree.field_nodes[idx].insertBook(b)

        ret = db.fields.find_one({"field":fn.name})
        if not ret:
            ret = {}
            ret['field'] = fn.name
            ret['books'] = books
        ret = db.fields.update({"field":fn.name}, ret, upsert=True)
        if not ret['ok']:
            logging.warn('write db.field error')
        # # 比较函数：按照专业度来排序（用户）；若a & b的专业度相同的话，就按照用户创建时间来排
        # def umodel_sort(a, b):
        #     aval = a['field_eval'][fn.name]
        #     bval = b['field_eval'][fn.name]
        #     if aval > bval:
        #         return 1
        #     elif aval == bval:
        #         adate = datetime.datetime.strptime(a['history_vec'][0]['date'], "%Y-%m-%d")
        #         bdate = datetime.datetime.strptime(b['history_vec'][0]['date'], "%Y-%m-%d")
        #         daydiff = (adate - bdate).days
        #         if daydiff > 0:
        #             return 1
        #         else:
        #             return -1
        #     else:
        #         return -1
 
        # # 首先根据这个节点标签, 按照field_eval[fn.name]对所有用户进行排序, 从小到大
        # # 然后根据用户的建立时间排序，也是从小到大
        # # fliter有专业向量嘅用户；
        # umodels = [ x for x in G_umodels.values() if 'field_eval' in x and fn.name in x['field_eval'] ]
        # #根据just嘅比较函数来排序
        # umodels.sort(cmp=umodel_sort, reverse=False)
        # logging.debug('=%s=SORTING field_nodes:%s, len of umodels:%d, ' % ('-'*1, fn.name, len(umodels)) )
        
        # #um：每个用户模型中的用户
        # for um in umodels: # 对于每个用户
        #     #raw_books: 啱先果啲排好序嘅用户嘅阅读历史
        #     raw_books = [ rsdb.findOneBook(x['book_id']) for x in G_historys[um['user_id']] if rsdb.findOneBook(x['book_id']) ]
        #     raw_books.sort(cmp=lambda a,b:cmp(a['rating']['average'], b['rating']['average']), reverse=True)
        #     #将书插入当前遍历节点
        #     for b in raw_books:
        #         ret = FieldTree.field_nodes[idx].insertBook(b)
        #         if ret:
        #             logging.debug('=%s=INSERT book %s' % ('-'*9, b['title']) )

    # # 输出每个节点的 书籍情况
    # for fn in FieldTree.field_nodes:
    #     logging.info('node:%s, %d books inserted.' % (fn.name, len(fn.books)) )


def Test(query, limit):
    N = 10 # 20 30 40
    # users_count = db.users.find(query, limit=limit).count()
    # print users_count
    T_Recall    = 0.0 
    T_Precision = 0.0
    for u in db.umodel.find():
        # if u['user_id'] not in G_umodels:
        #     continue
        train_idx = int( len(rsdb.findOneUser(u['user_id'])['history']) * TRAIN_RATIO )
        u_reads = set([unicode(x['book_id']) for x in rsdb.findOneUser(u['user_id'])['history']][:train_idx])
        # print '\nactually read:', ' '.join([rsdb.findOneBook(x)['title'] for x in u_reads if 'title' in rsdb.findOneBook(x)])
        rec_reads = set([ unicode(x[0]) for x in rsdb.findOneModel(u['user_id'])['interest_recbooks'] ])
        # print '\nrecommend read:', ' '.join([rsdb.findOneBook(x)['title'] for x in rec_reads if 'title' in rsdb.findOneBook(x)])
        Recall_    = float(len(u_reads&rec_reads)) / float((len(u_reads)+1))
        Precision_ = float(len(u_reads&rec_reads)) / float((len(rec_reads)+1))
        T_Recall += Recall_ 
        T_Precision += Precision_
        # if Recall_ == 0.0 or Precision_ == 0.0:
        #     users_count -= 1
        logging.info('Testing User %s u_read: %d, rec_reads: %d, Recall : %f%%, Precision : %f%%' 
            % (u['user_id'], len(u_reads), len(rec_reads), Recall_*100, Precision_*100) )
    logging.info('Testing total, Recall : %f%%, Precision : %f%%, F: %F%%' 
        % (T_Recall*100/limit, T_Precision*100/limit, (T_Recall*100/limit)/(T_Precision*100/limit) ) )

def main():
    # FieldTree.field_nodes = pickle.load(open('dump/FieldNodes'))
    #对阅读量大于15小于600的用户进行模型计算；将user表中的数据计算后保存到umodel表
    query = {'read':{'$gte':60, '$lte':600}}
    limit = 100
    generateUModelFromUsers(query, limit=limit)
    # #保存最新更新的专业树
    # # pickle.dump(FieldTree.field_nodes, open('dump/FieldNodes', 'w'))
    sortFieldNodeTree()
    generateRecBooksFromUModel()
    Test(query, limit=limit)
    # for fn in FieldTree.field_nodes:
    #     print '-'*10, fn.name
    #     for book in fn.books:
    #         print book['title']

if __name__ == '__main__':
    main()
    
