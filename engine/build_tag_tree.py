# -*- coding: utf-8 -*- 
from book_recsys import *
from Tag import Tag
from MI import MI
from HierarchicalClustering import *
from FieldTree import *


## 层次聚类时的迭代次数
HIERACHI_LEVEL = 243

## 同节点阀值
SAME_NODE_THRES = 0.95

## 子节点阀值
NEXT_NODE_THRES = 0.15
 
## 最小簇大小
MIN_CLUSTER_SIZE = 4



def build_tag_tree(domain):

    m = MI(domain)
    fields = {}

    # 相似度矩阵，利用互信息来计算
    mtrx = m.solveMImatrix()

    # 利用互信息相似矩阵计算互信息强度
    strg = dict( m.solveTagStrength(mtrx) )

    # 获得层次聚类结果, cluster_lst 是形如 [[],[],[],[]] 的列表的列表
    cluster_lst = build_hierachical_tags(mtrx, strg, HIERACHI_LEVEL, need_ask=False)
    for i,cluster in enumerate(cluster_lst):
        root_node = cluster[0]

        # 人工剪枝，问答模式
        question = u'[%s] - %s...(len:%d), Do You Want To (D)iscard? (%d/%d)'%(root_node, ' '.join(cluster[1:][:10]), len(cluster), i, len(cluster_lst))
        if len(cluster) < MIN_CLUSTER_SIZE or raw_input(question.encode("utf-8")).lower() == u'd':
            logging.warn('Discarded.')
            continue

        # 把每簇第一个节点加到fields上，称为簇的根节点
        fields[root_node] = {} 
        logging.debug( 'Elem: %s become root_node.' % root_node )

        getSim = lambda a,b:mtrx[a.split('`')[0]][b.split('`')[0]]

        # 递归遍历获得fields的节点, level是fields字典的其中一个值
        def addNode(node_to_add, level):
            share = True
            for child_node in level.keys():
                sim = getSim(child_node, node_to_add)
                if sim > SAME_NODE_THRES:

                    # 找到可以合并的节点，则不会再成为其他节点的子节点
                    level[child_node+'`'+node_to_add] = level[child_node].copy()
                    del level[child_node]

                    logging.debug( 'addNode Merge(%f): result:%s' %(sim, child_node+'`'+node_to_add) )
                    share = False
                    break # 原则上一个节点只会和一个节点合并

                elif sim > NEXT_NODE_THRES:

                    logging.debug( 'addNode %s Walk(%f): next child_node:%s ' %(node_to_add, sim, child_node) )
                    # 首先深度遍历寻找可以成为父亲的节点
                    level[child_node],shr = addNode(node_to_add, level[child_node])
                    if shr:
                        level[child_node][node_to_add] = {}
                        logging.debug( 'addNode %s Append(%f): next child_node:%s' % (node_to_add, sim, child_node))
                    share = shr
                # else:
                #     logging.debug( 'addNode Discard(%f): %s doesnt like child_node:%s' %(sim, node_to_add, child_node) )

            return level,share

        # 计算接下来的元素与第一个元素的相似度
        # 决定是属于同一个节点还是属于下一个节点
        for elem in cluster[1:]:

            # 计算元素与簇的根节点的相似度
            sim = getSim(root_node, elem)
            if sim > SAME_NODE_THRES:

                # 克隆一个分支并更名
                fields[root_node+'`'+elem] = fields[root_node].copy()
                del fields[root_node]
                root_node += '`'+elem

                logging.debug( 'Elem %s Merge(%f): root_node: %s.' % (elem, sim, root_node) )
            elif sim > NEXT_NODE_THRES:

                logging.debug( 'Elem %s Walk(%f): root_node: %s' % (elem, sim, root_node) )
                fields[root_node],share = addNode(elem, fields[root_node])
                if share: # 元素没有跟其中的任意深度子节点合并，则可以成为根节点的子节点
                    fields[root_node][elem] = {}
                    logging.debug( 'Elem %s Append(%f): root_node:%s' % (elem, sim, root_node) )
            else:
                logging.debug( 'Elem %s Discard(%f): root_node:%s' % (elem, sim, root_node) )
    return fields

def main():
    # domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.com-word2vec-1000.txt')]
    # domain = [x.name for x in FieldTree().field_nodes]
    fields = build_tag_tree(domain)

    ft = FieldTree(fields)


if __name__ == '__main__':
    main()