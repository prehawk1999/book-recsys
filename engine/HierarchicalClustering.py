# -*- coding: utf-8 -*- 
from book_recsys import *
from MI import MI
from FieldTree import *

class ClusterClass(object):

    mtrx = {}

    def __init__(self, tag):
        self.tags = [tag]

    def _addTags(self, tags):
        self.tags += tags

    def merge(self, inp_class):
        self._addTags(inp_class.tags)
        return self

    def getSim(self, inp_class):
        total = 0.0
        for t_1 in self.tags:
            for t_2 in inp_class.tags: 
                total += ClusterClass.mtrx[t_1][t_2]
        return total / len(self.tags) / len(inp_class.tags)

def getClosestCluster(mtrx):
    max_sim = 0.0
    a_cl = None
    b_cl = None
    for row_vec in mtrx.items():
        for col_vec in row_vec[1].items():
            if col_vec[1] > max_sim:
                max_sim = col_vec[1]
                a_cl = row_vec[0]
                b_cl = col_vec[0]
    return a_cl, b_cl

def shrinkCluster(inp_class, stop_idx=500, need_ask=True):
    count = 1
    while True:
        if len(inp_class) <= 2:
            return inp_class
        
        # 获得类簇之间的相似度
        tmp_mtrx = {}
        for inp_1 in inp_class:
            tmp_mtrx[inp_1] = {}
            for inp_2 in inp_class:
                if inp_1 == inp_2:
                    continue
                tmp_mtrx[inp_1][inp_2] = inp_1.getSim(inp_2)

        a_cl, b_cl = getClosestCluster(tmp_mtrx)
        if a_cl is None or b_cl is None:
            return inp_class
        inp_class.remove(a_cl)
        inp_class.remove(b_cl)
        inp_class.append(a_cl.merge(b_cl))
        # logging.info('getting new_cluster len:%d - [%s] - [%s]' % (len(inp_class), ' '.join(a_cl.tags), ' '.join(b_cl.tags)))
        
        # 首先比较标签的互信息强度，然后比较使用该标签的书籍数量，然后比较标签的使用次数
        def cmpf(a,b):
            if ClusterClass.strg[a['name']] > ClusterClass.strg[b['name']]:
                return 1
            elif ClusterClass.strg[a['name']] == ClusterClass.strg[b['name']]:            
                if len(a['book_ref']) > len(b['book_ref']):
                    return 1
                elif len(a['book_ref']) == len(b['book_ref']):
                    if a['count'] > b['count']:
                        return 1
                    else:
                        return -1
                else:
                    return -1
            else:
                return -1

        if need_ask:
            cond = lambda count:raw_input('lev:%d,next level?(enter) or finish?(q)'%count).lower()
        else:
            cond = lambda count:False

        # 停止条件，设置了迭代次数或者cmd中人工敲q
        ans = cond(count)
        if count >= stop_idx or ans == 'q':
            return inp_class

        # 假如设置了手动模式，则每次迭代都会输出聚类结果
        while ans:
            for i in inp_class:
                
                # 该簇的标签集合，然后对其进行排序，打印
                cs_i = [ rsdb.findOneTag(x) for x in i.tags ]
                cs_i.sort(cmp=cmpf, reverse=True)
                print 'getRankedItems: ', ' '.join([x['name']+unicode( ClusterClass(cs_i[0]['name']).getSim(ClusterClass(x['name'])) ) for x in cs_i])

            print 'new cluster: ', ' '.join(a_cl.tags)
            ans = cond(count)
            if ans == 'q':
                return inp_class

        count += 1

def build_hierachical_tags(mtrx, strg, stop_idx=500, need_ask=True):
    ClusterClass.mtrx = mtrx
    ClusterClass.strg = strg
    initClass = [ClusterClass(x) for x in mtrx.keys()]
    logging.debug('getting init class. len:%d' % len(initClass))
    cluster = shrinkCluster(initClass, stop_idx=stop_idx, need_ask=need_ask)
    ret_lst = []
    for c in cluster:
        ret_lst.append(c.tags)
    return ret_lst


def main():
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    # domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.com-word2vec-1000.txt')]
    # domain = [x.name for x in FieldTree().field_nodes]
    m = MI(domain)
    mtrx = m.solveMImatrix()
    strg = dict(m.solveTagRank(mtrx))      
    build_hierachical_tags(mtrx, strg)

if __name__ == '__main__':
    main()