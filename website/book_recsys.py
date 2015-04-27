# -*- coding: utf-8 -*- 

import math
import os,sys
import csv
import datetime
import logging
import pickle
from time import sleep  
import pymongo
from pymongo import MongoClient
from bson import ObjectId

# mongo数据库配置
conn = MongoClient('localhost',27017) 
db = conn.group_mems

# 日志模块配置
logging.basicConfig(level=logging.DEBUG,
                format='[%(asctime)s | %(funcName)s]: %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='log/Analysis.log',
                filemode='a')

console = logging.StreamHandler()

formatter = logging.Formatter('[%(asctime)s | %(funcName)s]: %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

PROG       = 100
PROG_REC   = 0 
PROG_SCALE = (0,10,20,30,40,50,60,70,80,90,100)

BOOK_DOMAIN = [u'技术', u'经济', u'文学', u'艺术', u'历史', u'文化', u'金融', u'漫画', u'法学']

DOMAIN = [u'程序设计', u'信息安全', u'人工智能', u'集体智慧', u'计算机硬件', u'计算机网络', u'计算机图像']

DOMAIN_TAG = [u'程序设计', u'调试', u'并发', u'版本控制', u'程序开发', 
u'前端开发', u'移动开发', u'多线程', u'云计算', u'编译原理', u'算法', 
u'信息安全', u'计算机安全', u'加密解密', u'密码学', u'人工智能', 
u'人机交互', u'机器学习', u'推荐系统', u'集体智慧', u'数据分析', 
u'回归分析', u'数值分析', u'单片机', u'嵌入式', u'硬件编程', u'嵌入式系统', 
u'计算机网络', u'网络协议', u'网络编程', u'计算机图像', u'机器视觉', u'数字图像处理', u'计算机视觉']


# 有缓存的数据库类，第一次访问的信息会被保存下来
class RecsysDatabase(object):

    def __init__(self):
        self.books_info   = {}
        self.users_info   = {}
        # self.umodel_info  = {}
        self.tags_info    = {}

    def findOneBook(self, book_id):
        if book_id in self.books_info:
            return self.books_info[book_id]
        else:
            book = db.books.find_one({"id":book_id})
            if book and 'title' in book:
                self.books_info[book_id] = book
                return book

    def findBooks(self):
        return self.books_info.values()

    def findOneUser(self, user_id):
        if user_id in self.users_info:
            return self.users_info[user_id]
        else:
            user = db.users.find_one({"user_id":user_id})
            if user:
                self.users_info[user_id] = user
                return user

    def findUsers(self):
        return self.users_info.values()

    def cacheUsers(self, user):
        if 'users_id' in user and user['user_id'] not in self.users_info:
            self.users_info['user_id'] = user

    def findOneTag(self, tag_id):
        if tag_id in self.tags_info:
            return self.tags_info[tag_id]
        else:
            tag = db.tags.find_one({"name":tag_id})
            if tag:
                self.tags_info[tag_id] = tag
                return tag

    def findTags(self):
        return self.tags_info.values()

    def findOneModel(self, mod_id):
        if mod_id in self.umodel_info:
            return self.umodel_info[mod_id]
        else:
            mod = db.umodel.find_one({"user_id":mod_id})
            if mod:
                self.umodel_info[mod_id] = mod
                return mod

# 标签标准化类
# transform
# transform_from_db
# simple_transform
class StandardTags(object):

    def __init__(self):
        self.rawtags = {}
        self.model = None
        self.start = None
        self.domain = None
        pass

    def _loadModel(self):
        if not self.model:
            self.model = gensim.models.Word2Vec.load("corpus/misc.model")

    def _loadRawtags(self): 
        if not self.rawtags:
            total = db.tags.count()
            for i,t in enumerate(db.tags.find()):
                self.rawtags[t['name']] = t
                prog_d('getting tags from mongo', i, total)
            
            self.root  = 0
            self._loadStart()
            for i in self.start:
                if i not in self.rawtags:
                    logging.warn('%s not in db.tags' % i)
                    continue
                self.root += len(self.rawtags[i]['book_ref'])

    def _loadStart(self):
        if not self.start:
            self.start = [i.strip().decode('utf-8') for i in open('log/tags.start.txt')]

    def _loadDomain(self):
        if not self.domain:
            self.domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]

    def transform_multi(self, input_tags, thres=0.01):
        self._loadRawtags()

        if isinstance(input_tags, list):
            normal = list(set(input_tags) - set(self.start))
        elif isinstance(input_tags, unicode):
            normal = [input_tags]
        if not normal:
            return input_tags
        # logging.debug('start appending db.tags.')
        # # tag = []
        # rawtags = {}
        # for t in db.tags.find():
        #     rawtags[t['name']] = t
        #     tag.append(t)
        # rawtags = dict([(i['name'], i) for i in tag]) 
        mtrx = self._solveMImatrix(start, normal)
        # pickle.dump(mtrx, open('dump/MImtrx.dmp', 'w'))
        # mtrx = pickle.load(open('dump/MImtrx.dmp'))

        ret = {}
        maximum = self._getMtrxMaxVec(mtrx)
        for val in maximum:
            if val[2] < thres:
                break
            ret.append(self.start[val[0]])
            if normal[val[1]] not in ret:
                ret[normal[val[1]]] = self.start[val[0]]
        return ret

    # 利用word2vec计算相似标签
    def similar(self, inp_tag, thres=0.01):
        self._loadModel()
        self._loadStart()
        ret_list = {}
        for tag in self.start:
            try:
                ret_list[tag] = self.model.similarity(tag, inp_tag)
            except:
                continue
        ret_list_item = ret_list.items()
        ret_list_item.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse=True)
        return [(x[0],x[1]) for x in ret_list_item if x[1] > thres]    

    ### 计算单个标签的最相似标准标签, 直接计算    
    def transform(self, inp_tag, thres=0.01):
        self._loadRawtags()
        self._loadStart()
        if inp_tag not in self.rawtags:
            return
        ret_list = {}
        for tag in self.start:
            a_set = set([x[0] for x in self.rawtags[tag]['book_ref']])
            b_set = set([x[0] for x in self.rawtags[inp_tag]['book_ref']])
            ret_list[tag] = self._calMIvalue(a_set, b_set)
        ret_list_item = ret_list.items()
        ret_list_item.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse=True)
        return [(x[0],x[1]) for x in ret_list_item if x[1] > thres]

    ### 计算单个标签的最相似标准标签, 从数据库获取, 默认thres = 0.01
    #@return list, 如果输入标签不是启动标签
    #@return unicode, 输入标签原样返回
    #@return None, 无效标签
    def transform_from_db(self, inp_tag):
        self._loadStart()
        if inp_tag in self.start:
            return inp_tag
        else:
            ret = rsdb.findOneTag(inp_tag)#}, {'standard':1})
            # print ret
            if ret and 'standard' in ret and ret['standard']:
                return ret['standard']

    # 永远只返回None或者最相似标签
    def simple_transform(self, inp_tag):
        ret = self.transform_from_db(inp_tag)
        if isinstance(ret, unicode):
            return ret
        elif isinstance(ret, list):
            return ret[0][0]

    # 把矩阵所有数字按照大小排列, 获取一个(x,y,value)的列表，标记坐标和值
    def _getMtrxMaxVec(self, mtrx):
        ret = []
        used_col = set()
        PROG = len(mtrx[0])
        for i in range( len(mtrx[0]) ):
            j = i % len(mtrx)
            rowmax = max(mtrx[j])
            if rowmax == -1:
                continue
            rowmax_idx = mtrx[j].index(rowmax)
            ret.append( (j, rowmax_idx, rowmax) )
            mtrx[j][rowmax_idx] = -1
            prog_d('_getMtrxMaxVec %f' % rowmax, i, PROG)
        ret.sort( cmp=lambda a,b: cmp(a[2], b[2]), reverse=True)
        return ret

    def _solveMImatrix(self, normal):
     
        MImatrix = []
        root = 0
        for i in (self.start+normal):
            if i not in self.rawtags:
                logging.warn('%s not in db.tags' % i)
                continue
            root += len(self.rawtags[i]['book_ref'])
     
        # c = 0
        # total = len(self.start)*len(normal)

        for i, st in enumerate(self.start):
            MImatrix.append([])
            for j, t in enumerate(normal):
                st_set = set([x[0] for x in self.rawtags[st]['book_ref']])
                if t in self.rawtags:
                    t_set  = set([x[0] for x in self.rawtags[t]['book_ref']])
                    MImatrix[i].append(self._calMIvalue(st_set, t_set, root))
                else:
                    MImatrix[i].append(0.0)
                # prog_d('solve Matrix row', c, total)
                # c += 1
            
        return MImatrix

    def _calMIvalue(self, a_set, b_set):
        pab = math.fabs(float(len(a_set&b_set)) / self.root)
        pa  = math.fabs(float(len(a_set)) / self.root)
        pb  = math.fabs(float(len(b_set)) / self.root)
        Iab = pab * math.log((pab+1) / (pa*pb))
        Ha  = -pa * math.log(pa)
        Hb  = -pb * math.log(pb)
        return float(Iab) / (float(Ha + Hb) / 2)


# set PROG before using this function
def prog_d(dstr, line=-1, total=100):
    global PROG_REC
    if line >= 0:
        progress = int(float(line)/float(total) * 100 + 1)
        if progress not in PROG_SCALE or progress == PROG_REC:
            return
        # print progress
        PROG_REC = progress
        dstr += ' %d%%(%d/%d)' % (progress, line, total)
        logging.info('=%s='%progress + dstr)
    else:
        logging.info('=%s= Finishing ' + dstr)

### 计算用户相似度，利用余弦公式, a和b向量是维度和元素都是相同的
def getCosSim(a_vec, b_vec):
    RU = 0.0
    Ra = 0.0
    Rb = 0.0
    for k in a_vec.keys():
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


def getLines(inpfile):
    count = -1
    for count,line in enumerate(open(inpfile,'rU')):  
        pass      
    count += 1
    return count

rsdb   = RecsysDatabase()
stdtag = StandardTags()

if __name__ == '__main__':
    pass