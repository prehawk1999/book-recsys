# -*- coding: utf-8 -*- 
from book_recsys import *

        

class Tag(object):

    tdata = {}
    def __init__(self, tagvec):
        self.tagvec = set(tagvec)
        if not Tag.tdata:
            total = db.tags.count()
            for i,tag in enumerate(db.tags.find(timeout=False)):
                Tag.tdata[tag['name']] = tag
                prog_d('getting tags from mongo', i, total)
        for t in tagvec:
            if t not in Tag.tdata:
                self.tagvec.remove(t)
                

    # 计算标签 - 物品矩阵
    def solveItemMtrx(self):
        mtrx = {}
        for tag in self.tagvec:
            mtrx[tag] = {}
            tag_info = Tag.tdata[tag]
            for br in tag_info['book_ref']:
                # book_id br[0]
                # tf br[3]
                mtrx[tag][br[0]] = br[3] * tag_info['idf']
        return mtrx

    # 获得tagvec输入标签列表的相似度矩阵，利用标签 - 物品矩阵进行余弦相似度计算
    def solveCosSimMtrx(self):
        tag_item_mtrx = self.solveItemMtrx()
        mtrx = {}
        for tag_i in self.tagvec:
            mtrx[tag_i] = {}
            for tag_j in self.tagvec:
                sim = getCosSim( tag_item_mtrx[tag_i], tag_item_mtrx[tag_j] )
                mtrx[tag_i][tag_j] = sim

        return mtrx

    # 根据输入的标签相似度矩阵计算每个标签对其他所有标签的强度
    def solveTagRank(self, mtrx):
        ret = {}
        # mtrx = self.solveCosSimMtrx()
        for t in self.tagvec:
            acc = 0.0
            for v in mtrx[t].values():
                acc += v
            ret[t] = acc
        return getRankedItems(ret)




def main():
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    tagg = Tag(domain)
    mtrx = tagg.solveCosSimMtrx()
    for i,v in tagg.solveTagRank(mtrx):
        print i,v
    # mtrx = tagg.solveCosSimMtrx()
    # for domtag in mtrx.items():
    #     domtag_lst = domtag[1].items()
    #     domtag_lst.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
    #     print domtag[0], ' '.join([ unicode(x[0])+unicode(x[1]) for x in domtag_lst if x[0] != domtag[0]][:7])


if __name__ == '__main__':
    main()