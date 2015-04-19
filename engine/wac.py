# -*- coding: utf-8 -*- 
from book_recsys import *
from stdtag import StandardTags
# word2vec = pickle.load(open('dump/Word2VecMtrx.dmp'))


stdtag = StandardTags()
stdtag._loadStart()

def _accWeight(node_dict, level, fno, a=0.0):
    up_lev = {}
    for nd in node_dict.items():
        p_mat = level[fno][2]
        for upnd in p_mat[nd[0]].items(): # 遍历连接着的上层节点
            if upnd[1] > 0:
                if upnd[0] not in up_lev:
                    up_lev[upnd[0]] = 0.0
                up_lev[upnd[0]] += nd[1]*upnd[1]*(1+a) # 权重叠加
    return up_lev

def findLevel(tag, level):
    for i, lev in enumerate(level):
        if tag in lev[0]:
            return i

def getWacWeight(tag, level, iter_level=-1):
    #print '\r\n\r\n\r\n\r\n', tag
    if iter_level == -1:
        iter_level = len(level)-1
    ret = {}
    num = findLevel(tag, level)

    if tag in level[0][2]:
        node_dict = {tag:1}
        ### 从底层开始遍历
        for fno in range(len(level)-1):
            node_dict = _accWeight(node_dict, level, fno, 0.3)
            if fno > iter_level:
                ret = node_dict
                break

    for w in ret.items():
        idf = db.tags.find_one({"name":w[0]}, {"idf":1})['idf']
        ret[w[0]] = w[1]*float(idf)
    return ret

### 按照多到少的节点数排列
def loadLevel():
    level = []
    for num in range(100):
        # 第0层为所有节点
        f = 'dump/waclevel%d.dmp' % int(num+1)
        # print f
        if os.path.exists(f):
            level.append(pickle.load(open(f)))
        prog_d('level append', num, 100)    
    return level

def loadAssoStren():
    return pickle.load(open('dump/assostren.dmp'))


def print_wac(tag,level,iter):
    weight = getWacWeight(tag, level, iter)
    print '='*10, tag, '='*10
    if not weight:
        return
    # for w in weight.items():
    #     idf = db.tags.find_one({"name":w[0]}, {"idf":1})['idf']
    #     weight[w[0]] = w[1]*float(idf)
    weight_lst = weight.items()
    weight_lst.sort(cmp=lambda a,b:cmp(a[1],b[1]),reverse=True)
    for w in weight_lst:
        print w[0], w[1], findLevel(w[0], level)

def test_wac_weight():
    level = loadLevel()
    for test_tag in [u'数据处理', u'嵌入式', u'电影']:
        print_wac(test_tag,level,3)

if __name__ == '__main__':
    logging.info("running %s" % ' '.join(sys.argv))
    
    # test_wac_weight()
    # test_recog_rate()
    # buildAssoStren()
