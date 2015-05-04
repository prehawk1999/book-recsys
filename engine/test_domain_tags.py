# -*- coding: utf-8 -*- 
from book_recsys import *
from MI import MI
from build_wac_tree import *
from FieldTree import *

def main():
    # 计算机领域标签
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    # test_tree = FieldTree()
    # domain = [x.name for x in test_tree.field_nodes]
    # m = MI(domain)
    # m.enable_idf()
    # mtrx = m.solveMatrix()
    # model = gensim.models.Word2Vec.load("corpus/misc.model")
    model = gensim.models.Word2Vec.load('corpus/book.model')
    mtrx = solveWord2VecMatrix(domain, model)
    pickle.dump(mtrx, open('dump/word2vecmtrx.dmp', 'w'))

    # k = KNN(mtrx)
    # k.setInitClass()
    # ret = k.getCluster()
    # print ret
    for domtag in mtrx.items():
        domtag_lst = domtag[1].items()
        domtag_lst.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
        print domtag[0], ' '.join([ unicode(x[0])+unicode(x[1]) for x in domtag_lst][1:7])

    # solveWACmatrix(mtrx, 0.9)





if __name__ == '__main__':
    main()