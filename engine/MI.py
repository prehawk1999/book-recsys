# -*- coding: utf-8 -*- 
from book_recsys import *

class MI:

	def __init__(self, tagvec):
		self.taginfo    = {}
		self.tagvec     = tagvec
		self.idf_weight = False

	def enable_idf(self):
		self.idf_weight = True

	def _loadTagInfo(self):
	    self.taginfo = {}
	    total = db.tags.count()
	    for i,tag in enumerate(db.tags.find(timeout=False)):
	        self.taginfo[tag['name']] = tag
	        prog_d('getting tags from mongo', i, total)

	def solveMatrix(self):
		if not self.taginfo:
			self._loadTagInfo()
		return self._svDICT()

	def _svLIST(self):
	    MImatrix = []
	    root = 0
	    for tag in self.tagvec:
	        if tag not in self.taginfo:
	            logging.warn('%s not in db.tags' % tag)
	            continue
	        root += len(self.taginfo[tag]['book_ref'])

	    for i, st in enumerate(self.tagvec):
	        MImatrix.append([])
	        for j, t in enumerate(self.tagvec):
	            st_set = set([x[0] for x in self.taginfo[st]['book_ref']])
	            if t in self.taginfo:
	                t_set  = set([x[0] for x in self.taginfo[t]['book_ref']])
	                MImatrix[i].append(calMIvalue(st_set, t_set, root))
	            else:
	                MImatrix[i].append(0.0)
	       
	    return MImatrix

	def _svDICT(self):
	    retmatrix = {}
	    root = 0
	    for tag in self.tagvec:
	        if tag not in self.taginfo:
	            logging.warn('%s not in db.tags' % tag)
	            continue
	        root += len(self.taginfo[tag]['book_ref'])
	    
	    for i, st in enumerate(self.tagvec):
	        retmatrix[st] = {}
	        for j, t in enumerate(self.tagvec):
	            st_set = set([x[0] for x in self.taginfo[st]['book_ref']])
	            st_idf = self.taginfo[st]['idf']
	            if t in self.taginfo:
	                t_set  = set([x[0] for x in self.taginfo[t]['book_ref']])
	                if self.idf_weight:
	                	w = st_idf * self.taginfo[t]['idf']
	                else:
	                	w = 1
	                retmatrix[st][t] = self._calMI(st_set, t_set, root) * w
	            else:
	                retmatrix[st][t] = 0.0
	       
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
    m.enable_idf
    mtrx = m.solveMatrix()
    for domtag in mtrx.items():
        domtag_lst = domtag[1].items()
        domtag_lst.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
        print domtag[0], ' '.join([ unicode(x[0])+unicode(x[1]) for x in domtag_lst][1:7])
    


if __name__ == '__main__':
	main()