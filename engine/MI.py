# -*- coding: utf-8 -*- 
from book_recsys import *
from Tag import Tag

class MI(Tag):

    def __init__(self, tagvec):
        super(MI, self).__init__(tagvec)
        self.tagMI      = {}
        self.tagMImtrx    = {}
        self.idf_weight = False

    def enable_idf(self):
        self.idf_weight = True

    def solveMImatrix(self):
        return self._svDICT()

    def getTagsMI(self):
        if self.tagMI:
            return self.tagMI
        self.solveMImatrix()
        for t in self.tagMImtrx.keys():
            MI = 0.0
            for x in self.tagMImtrx[t].values():
                MI += x
            self.tagMI[t] = MI
        return self.tagMI

    def _svLIST(self):
        MImatrix = []
        root = 0
        for tag in self.tagvec:
            if tag not in Tag.tdata:
                logging.warn('%s not in db.tags' % tag)
                continue
            root += len(Tag.tdata[tag]['book_ref'])

        for i, st in enumerate(self.tagvec):
            MImatrix.append([])
            for j, t in enumerate(self.tagvec):
                st_set = set([x[0] for x in Tag.tdata[st]['book_ref']])
                if t in Tag.tdata:
                    t_set  = set([x[0] for x in Tag.tdata[t]['book_ref']])
                    MImatrix[i].append(calMIvalue(st_set, t_set, root))
                else:
                    MImatrix[i].append(0.0)
           
        return MImatrix

    def _svDICT(self):
        if self.tagMImtrx:
            return self.tagMImtrx
        retmatrix = {}
        root = 0
        for tag in self.tagvec:
            if tag not in Tag.tdata:
                logging.warn('%s not in db.tags' % tag)
                continue
            root += len(Tag.tdata[tag]['book_ref'])
        
        for i, st in enumerate(self.tagvec):
            retmatrix[st] = {}
            for j, t in enumerate(self.tagvec):
                st_set = set([x[0] for x in Tag.tdata[st]['book_ref']])
                st_idf = Tag.tdata[st]['idf']
                if t in Tag.tdata:
                    t_set  = set([x[0] for x in Tag.tdata[t]['book_ref']])
                    if self.idf_weight:
                        w = st_idf * Tag.tdata[t]['idf']
                    else:
                        w = 1
                    retmatrix[st][t] = self._calMI(st_set, t_set, root) * w
                else:
                    retmatrix[st][t] = 0.0
           
        self.tagMImtrx = retmatrix
        return retmatrix

    def _calMI(self, a_set, b_set, root):
        pab = math.fabs(float(len(a_set&b_set)) / root)
        pa  = math.fabs(float(len(a_set)) / root)
        pb  = math.fabs(float(len(b_set)) / root)
        Iab = pab * math.log((pab+1) / (pa*pb))
        Ha  = -pa * math.log(pa)
        Hb  = -pb * math.log(pb)
        return float(Iab) / (float(Ha + Hb) / 2)

def main():
    # 计算机领域标签
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    m = MI(domain)
    mi_dict = m.getTagsMI()
    mi_vec = mi_dict.items()
    mi_vec.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
    for i in mi_vec:
        print i[0], i[1]
    return
    mtrx = m.solveMImatrix()
    for domtag in mtrx.items():
        pass
        # domtag_lst = domtag[1].items()
        # domtag_lst.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
        # print domtag[0], ' '.join([ unicode(x[0])+unicode(x[1]) for x in domtag_lst][1:7])
        # print domtag[0], m.getTagMI(domtag[0])


if __name__ == '__main__':
    main()