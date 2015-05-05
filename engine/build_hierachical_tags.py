# -*- coding: utf-8 -*- 
from book_recsys import *
from MI import MI
from FieldTree import *

class ClusterClass(object):

	taginfomtrx = {}

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
				total += ClusterClass.taginfomtrx[t_1][t_2]
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

def shrinkCluster(inp_class):
	if len(inp_class) > 2:
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
		logging.info('getting new_cluster len:%d - [%s] - [%s]' % (len(inp_class), ' '.join(a_cl.tags), ' '.join(b_cl.tags)))
		inp_class.append(a_cl.merge(b_cl))
		return shrinkCluster(inp_class)
	else:
		return inp_class

def build_hierachical_tags(mtrx):
	ClusterClass.taginfomtrx = mtrx
	initClass = [ClusterClass(x) for x in mtrx.keys()]
	logging.debug('getting init class. len:%d' % len(initClass))
	shrinkCluster(initClass)


def main():
    domain = [i.split(' ')[0].decode('utf-8') for i in open('log/tag.domain-classify.txt')]
    # test_tree = FieldTree()
    # domain = [x.name for x in test_tree.field_nodes]
    m = MI(domain)
    # m.enable_idf()
    mtrx = m.solveMatrix()
    build_hierachical_tags(mtrx)



if __name__ == '__main__':
	main()