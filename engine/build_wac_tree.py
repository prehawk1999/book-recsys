# -*- coding: utf-8 -*- 
from book_recsys import *
from stdtag import StandardTags
import gensim

stdtag = StandardTags()


def solveWord2VecMatrix(starttags, model):
    lines = len(starttags)*len(starttags)
    mtrx = {}
    # 计算相似度矩阵
    c = 0
    for k in starttags:
        try:
            model.similarity(u"C", k)
            if k not in mtrx:
                mtrx[k] = {}
            for l in starttags:
                try:
                    model.similarity(u"C", l)
                    mtrx[k][l] = model.similarity(k,l)
                    c += 1
                    prog_d('%s %s %f similarity count' % (k,l,mtrx[k][l]), c, lines)
                except:
                    continue
        except:
            continue
    return mtrx
    
def getCluster(b,d, mtrx):
    return b

def solveWACmatrix(mtrx, T=0.9):
    # 1-15 T=1, 15-44 T=0.9
    for i in range(50):
        if os.path.exists('dump/waclevel%d.dmp' % int(i+1)):
            continue
        if i == 0:
            b = mtrx
        else:
            b = pickle.load(open('dump/waclevel%d.dmp' % int(i)))[1]
        # {tag_name：degree},{tag1:{tag1:degree}}, {tag1:{tag:degree}}   
        a,b,c = buildUpperLevel(b, T)

        pickle.dump((a,b,c), open('dump/waclevel%d.dmp' % int(i+1), 'w'))
        prog_d('dump/waclevel%d.dmp' % int(i+1))

# 构建上一层节点，返回值全部是字典，用于保存对应关系
# @param Wl: 二维dict，原始数据，存放相似度矩阵
# @return Vh： 一维dict，存放上一层点集tuple列表，(tag_name, degree)
# @return Wh：二维dict，存放本层相似度矩阵 Eh通过Wh和阀值（0.0001）来确定
# @return Pl： 二维dict(不等边)，存放插值矩阵，上层跟下层的关系, 同样用阀值(0.0001)确定边的存在
def buildUpperLevel(Wl, T):
    # global PROG

    # 计算v跟vset的degree，即v跟vset里的每一个节点的相似度累加，数据来自mtrx
    def calDegree(v, vset):
        ret = 0.0
        for l in vset:
            if v != l[0]:
                ret += l[1]
        return ret

    ### 第一步，生成上层顶点集
 
    # 计算所有标签的度：标签跟当层所有其他标签的相似度累加
    # 把节点降序排列，根据阀值筛选degree，挑选Vl的上一层节点Vh出来
    degree = {} # dict([ (x[0], ) for x in Vh.items() ])
    for i,k in enumerate(Wl.items()):
        degree[k[0]] = calDegree(k[0], k[1].items())
    VlItems = degree.items()
    VlItems.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse=True)
    logging.debug('\rsorted VlItems full display: %s' % ' '.join([x[0] for x in VlItems]))

    # 取Vl的第一个作为Vl的上一层Vh节点
    VhItems = []
    VhItems.append(VlItems[0])
    for i, v in enumerate(VlItems):
        prog_d('generate Vh nodes.', i, len(VlItems))
        if i == 0:
            continue
        if calDegree(v, VhItems) <= calDegree(v, VlItems) * T: # 非强连接加入Vh中
            VhItems.append( VlItems[i] )

    Vh = dict(VhItems)
    Vl = dict(VlItems)

    ### 第二步，建立两个顶点集的关系, 通过插值矩阵来刻画
    # 先将Wl转化为普通数组形式
    Wlist = []
    for i,k in enumerate(Wl.items()):
        Wlist.append([])
        for l in k[1].items():
            Wlist[i].append(Wl[k[0]][l[0]])

    Pl = []
    Pl_ret = {}
    prog = len(Vh)*len(Vl)
    c = 0
    logging.debug('start generating pl mtrx. %d ' % prog)
    for i,k in enumerate(Vl.keys()):
        Pl.append([])   
        if k not in Pl_ret:
            Pl_ret[k] = {}
        for j,l in enumerate(Vh.keys()):

            # 建立插值稀疏矩阵
            if k in Vh and l in Vh:
                if k == l:
                    Pl[i].append(1)
                    Pl_ret[k][l] = 1
                else:
                    Pl[i].append(0)
                    Pl_ret[k][l] = 0
            elif k in Vl:
                Pl[i].append( Wl[k][l] / calDegree(k, VhItems) )
                Pl_ret[k][l] = Wl[k][l] / calDegree(k, VhItems) 
            prog_d('create P matrix', c, prog)
            #print c
            c += 1
 
    # 第三步 建立上一层的相似性矩阵Wh
    Wh = numpy.mat(Pl).T * numpy.mat(Wlist) * numpy.mat(Pl)

    # 第四步 生成边集，保存字典形式的矩阵
    Wh_ret = {}
    logging.debug('start saving mtrx.')
    for i,row in enumerate(Wh.A):
        for j,val in enumerate(row):
            # 初始化第二维字典
            if VhItems[i][0] not in Wh_ret:
                Wh_ret[VhItems[i][0]] = {}
            Wh_ret[VhItems[i][0]][VhItems[j][0]] = val

    return Vh, Wh_ret, Pl_ret

def build_wac_tree(T):

    # starttags = stdtag._loadStart()
    model = gensim.models.Word2Vec.load("corpus/misc.model")

    # 载入领域相关标签
    stdtag._loadDomain()

    # 获得第一层相似度矩阵
    if os.path.exists('dump/word2vecmtrx.dmp'):
        mtrx = pickle.load(open('dump/word2vecmtrx.dmp'))
    else:
        mtrx = solveWord2VecMatrix(stdtag.domain, model)
        pickle.dump(mtrx, open('dump/word2vecmtrx.dmp', 'w'))

    # 以第一层相似度矩阵为输入，构建wac树，结果存放到dump/waclevel%d 里
    solveWACmatrix(mtrx, T)

if __name__ == '__main__':
    
    # check and process input arguments
    if len(sys.argv) < 2:
        print 'usage: python build_wac_tree.py <T>'
        sys.exit(1)
    T = sys.argv[1]
    build_wac_tree(float(T))