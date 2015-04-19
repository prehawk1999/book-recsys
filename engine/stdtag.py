# -*- coding: utf-8 -*- 
from book_recsys import *
import gensim

# rsdb = RecsysDatabase()#

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

def test_get_standard_tags(uid='dearcloud'):

    # tags = getTagsFromUser(uid)
    stdtag = StandardTags()
    for t in [u'穆斯林',u'刘慈欣', u'土耳其']:
        tgcl = stdtag.transform(t, 0.001)
        if tgcl:
            for tc in tgcl:
                print tc[0], tc[1]
        print '\r\n'


def test_transform_from_db():
    stdtag = StandardTags()
    for t in [u'当代小说', u'好爸爸', u'围棋']:
        ret = stdtag.simple_transform(t)
        print ret

if __name__ == '__main__':
    # update_standard_tags()
    test_transform_from_db()
