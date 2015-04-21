# -*- coding: utf-8 -*- 
from book_recsys import *
from GetWacWeight import getWacWeight, loadLevel, print_wac #getWordWeight
from stdtag import StandardTags
# from GetBookModel import getBookModel


# stdtag = StandardTags()
# rsdb   = RecsysDatabase()
stdtag._loadStart()

## 用户标注标签对兴趣模型的权重
USER_TAG_W = 2

##书籍原有标签对兴趣模型的权重
BOOK_TAG_W = 1

## 用户相似度阀值
USER_SIM_THRES = 1500.0

## 书籍推荐评分数量限制
BOOK_REC_NUM = 10

## 用户专业度阀值，低于这个阀值的用户将不归类到这个专业里
PRO_THRES      = 0

## 专业书籍推荐数量
PRO_RECOMM_NUM = 60

## 根据专业度选择近邻的上限和下限
PRO_SIM_RECORD_CEILING   = 50
PRO_SIM_RECORD_FLOOR     = 5

def getModelUsersHistory():
    users = {}
    for u in db.umodel.find():
        users[u['user_id']] = db.users.find_one({"user_id":u['user_id']})['history']
    return users 

umodels  = loadUModels() 
PRO_VEC = pickle.load(open('dump/provec.dmp'))

### 用户模型表umodel
#   通过阅读历史计算的模型增量
#   用户模型更新时间updatetime: 
def updateUserModel(user, nowtime, utype):
    count = 0

    # user表中的记录表和umodel表中的长度不同则优先计算user表中剩下的history
    # 否则如果更新时间有差异更新所有umodel中的条目
    umodel = db.umodel.find_one({"user_id":user['user_id']})
    if umodel:
        if len(umodel['history_vec']) != len(user['history']):
            count = len(umodel['history_vec'])
        elif (nowtime - umodel['uptime']).days == 0:
            logging.info('user %s model is up to date.' % umodel['user_id']) # 通过user表来更新umodel表
            return
        logging.info('update user %s model - umodel len: %d, history len: %d' 
            % (user['user_id'], len(umodel['history_vec']), len(user['history'])) )
        u_id = umodel['_id']
    else:
        umodel = {'history_vec':[], 'uptime':nowtime, 'user_id':user['user_id'], 'type':utype}
        u_id = db.umodel.insert(umodel)
        logging.info('create user %s model _id %s' % (user['user_id'], u_id) )
        
    umodel['interest_eval'] = {}
    umodel['pro_eval'] = dict( [(x, 0.0) for x in DOMAIN_TAG] )

    # 遍历用户阅读历史
    for h in user['history'][count:]:
        interest_vec, pro_vec = getVecByHistory(h)
        history_vec  = {"date" : h['date'], "interest_vec" : interest_vec, "pro_vec" : pro_vec}
        umodel['history_vec'].append(history_vec)

        # 累加最终兴趣向量
        for t in interest_vec.items():
            if t[0] not in umodel['interest_eval']:
                umodel['interest_eval'][t[0]] = 0.0
            umodel['interest_eval'][t[0]] += getEbbinghausVal(nowtime, h['date']) * t[1]

        # 累加最终专业向量
        for t in pro_vec.items():
            umodel['pro_eval'][t[0]] += math.log( pro_vec[t[0]] + 1 )
            # print umodel['pro_eval'][t[0]]
             
        db.umodel.update({"_id":u_id}, {"$addToSet":{"history_vec":history_vec}})
        # logging.info('-=-=-=INSERT-=-=-=- history_vec interest %s, pro %s, on date %s' % (' '.join([unicode(x[0])+unicode(x[1]) for x in interest_vec.items()]), ' '.join([unicode(x[0])+unicode(x[1]) for x in pro_vec.items()]), h['date']) )

    umodel['uptime'] = nowtime
    db.umodel.update({'_id':u_id}, umodel, upsert=True)
    logging.info('-=-=-=- evaluate -=-=-=- final vector: ||interest|| %s, ||pro|| %s' 
        % (' '.join([unicode(x[0])+unicode(x[1]) for x in umodel['interest_eval'].items()]), ' '.join( [unicode(x[0])+unicode(x[1]) for x in umodel['pro_eval'].items()] )) )

### 根据每条历史获得兴趣向量, 专业模型
def getVecByHistory(history):

    # 兴趣向量，用用户的标签标示
    intVec = {}

    # 专业向量的表示：{所属领域：专业度，阅读量}
    proVec = dict( [(x, 0.0) for x in DOMAIN_TAG] )

    # 根据用户显式标注的标签来累加兴趣向量，但是对专业向量没有影响
    if 'tag' in history:
        for usertag in history['tags']:
            realtag = stdtag.simple_transform(usertag)
            if realtag and realtag.find('.') == -1:

                # 获得标签的idf
                ret = rsdb.findOneTag(realtag)
                if ret:
                    tag_idf = ret['idf']
                else:
                    tag_idf = 1
                    logging.warn('tag %s get idf error.' % realtag)

                if realtag not in intVec:
                    intVec[realtag] = 0
                intVec[realtag] += USER_TAG_W * tag_idf

    # 根据书籍所拥有的8个标签来累加兴趣向量和专业向量
    book = rsdb.findOneBook(history['book_id'])
    if book:
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

                if realtag not in intVec:
                    intVec[realtag] = 0
                intVec[realtag] += BOOK_TAG_W * tag_idf

                # # 累加专业模型
                if realtag not in PRO_VEC:
                    continue
                proVec[PRO_VEC[realtag][0]] += float(PRO_VEC[realtag][1])
                # logging.info('user: [%s] book: [%s] tag:[%s] [%s] provec: %s - %f' 
                #     % (history['user_id'], book['title'], booktag, realtag, PRO_VEC[realtag][0], PRO_VEC[realtag][1]) )
        # 只根据书籍的domain累加
        # if 'domain' in book and book['domain']:
        #     proVec[book['domain'][0][0]] = book['domain'][0][1]
        #     logging.info('%s %s provec: %s - %f' 
        #         % (history['user_id'], book['title'], book['domain'][0][0], book['domain'][0][1]) )

    return intVec, proVec

### 根据艾宾浩斯遗忘公式，计算两个日子间隔表示的时间系数
def getEbbinghausVal(nowtime, history_date, c=1.25, k=1.84):
    timediff = nowtime - datetime.datetime.strptime(history_date, "%Y-%m-%d")
    return float(k)/float(math.log(timediff.days)**c+k)


def main():

    query = {'read':{'$gte':15, '$lte':15}}
    total = db.users.find(query).count()
    for i,u in enumerate( db.users.find(query) ):
        print u
        updateUserModel(u, datetime.datetime(2015,4,1), 'recsys')
        # break

    users_his = getModelUsersHistory()
    standard_start = dict([(x,0) for x in stdtag.start])
    # umodels = []
    umodel_books = set()
    for u in db.umodel.find(timeout=False):

        # 记录所有umodel的user所阅读的书籍
        for h in users_his[u['user_id']]:
            umodel_books.add(h['book_id'])

        if 'interest_eval' not in u:
            continue

        ## 获得根据用户兴趣向量的推荐书籍, 需要排除已阅读书籍
        user_books = []
        for b in loadBookLst():
            weight = 0.0
            for t in b['tags']:
                if t['name'] in u['interest_eval'].keys():
                    weight += u['interest_eval'][t['name']]
            if b['id'] not in [ x['book_id'] for x in users_his[u['user_id']] ]:
                user_books.append( (b['id'], weight, b['title']) )
                if len(user_books) > BOOK_REC_NUM:
                    break

        user_books.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
        u['interest_recbooks'] = user_books

        ## 获得根据用户专业向量的推荐书籍
        # 获得用户的专业近邻用户
        user_sim_list = [ (u['user_id'], 1.0) ]
        for v in db.umodel.find():
            if 'interest_eval' not in v: 
                continue
            similarity = getCosSim(u['pro_eval'], v['pro_eval'])
            if similarity > USER_SIM_THRES:
                user_sim_list.append( (v['user_id'], similarity) )
                # logging.debug('\nuser_u:[%s] - %r, \nuser_v:[%s] - %r, \n%f, ' 
                #     % (u['user_id'], u['pro_eval'].values(), v['user_id'], v['pro_eval'].values(), similarity) )
        user_sim_list.sort(cmp=lambda a,b: cmp(a[1], b[1]), reverse=True)
        u['sim_users'] = user_sim_list
        # logging.debug('user_sim_list len: %d' % len(user_sim_list) )

        ## slope one 算法数据准备, 评分和阅读量，评分差矩阵            
        # 获得近邻用户和输入用户阅读的本领域书籍
        comm_read = set() # book_id
        self_read = set() # book_id：rate
        # other_read  = set()
        for um in user_sim_list: # um[0] user_id, um[1] similarity
            for x in users_his[um[0]]:
                binfo = rsdb.findOneBook(x['book_id'])
                if not binfo or 'domain' not in binfo:
                    continue
                if not binfo['domain']:
                    continue
                comm_read.add( x['book_id'] )
                if um[0] == u['user_id']:
                    self_read.add( x['book_id'] )
        logging.debug('user %s, sim_users len: %d, comm_read len:%d self_read len:%d\r\n\r\n ' % (u['user_id'], len(user_sim_list), len(comm_read), len(self_read)) )

        # 获得comm_read的近邻用户书籍平均评分和评分人数
        avg_rate = {}
        for bid in comm_read:

            # 计算平均评分
            accrate = 0 
            readers = 0
            for um in user_sim_list:
                if bid in [ x['book_id'] for x in users_his[um[0]] ]: # 用户看过
                    ret = [x['rate'] for x in users_his[um[0]] if x['book_id'] == bid][0]
                    if int(ret) == 0:
                        continue
                    accrate += int(ret)
                    readers += 1
            if readers != 0:
                avgrate = float(accrate) / float(readers)
                avg_rate[bid] = [avgrate, readers]
            else:
                avg_rate[bid] = [0,0]

        # 构造评分差矩阵    
        dev_mtrx = dict([(x,{}) for x in avg_rate.keys()])
        for dev in dev_mtrx.keys():
            # print avg_rate[dev][0] - avg_rate[x[0]][0]
            dev_mtrx[dev] = dict([ ( x[0], avg_rate[dev][0] - avg_rate[x[0]][0] ) for x in avg_rate.items() ]) 

        # 计算对于输入用户所有本领域的书籍平均分, 
        book_rate = dict([ (x, 0.0) for x in comm_read if x not in self_read ]) # book_id, rate
        for br in book_rate.keys():
            rate = 0.0
            if self_read:
                for sr in self_read:
                    rate += dev_mtrx[sr][br]
                book_rate[br] = rate / len(self_read)
            else:
                book_rate[br] = 0

        pro_recomm = book_rate.items()
        pro_recomm.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
        pro_recomm = pro_recomm[:PRO_RECOMM_NUM]
        logging.info('pro_recomm len: %d' % len(pro_recomm))
        u['pro_recbooks'] = pro_recomm
        for pr in pro_recomm:
            book = rsdb.findOneBook(pr[0])
            if book and pr[1] > 0:
                print book['title'], pr[1]

        ## 写入用户最终推荐书目
        ret = db.umodel.update({"_id":u['_id']}, u)
        logging.info('update user recommend books %s' % u['user_id'] )

if __name__ == '__main__':
    main()
    
