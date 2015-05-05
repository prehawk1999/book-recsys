# -*- coding: utf-8 -*- 
from book_recsys import *
from MI import MI
from HierachicalClustering import *


## 层次聚类时的迭代次数
HIERACHI_LEVEL = 246

## 同节点阀值
SAME_NODE_THRES = 0.9

## 子节点阀值
NEXT_NODE_THRES = 0.21


def main():
    # domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.com-word2vec-1000.txt')]

    # mtrx 
    # strg
    build_hierachical_tags(mtrx, strg, HIERACHI_LEVEL, need_ask=False)

if __name__ == '__main__':
	main()