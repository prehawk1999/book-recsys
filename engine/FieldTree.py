# -*- coding: utf-8 -*- 
from book_recsys import *


FIELDS = {
	u'计算机`计算机科学`计算机技术':{ # 0
		u'程序设计`编程`程序开发`编程语言`programming':{#3
			u'c/c++`c`c++`c语言':{#11
				u'stl':{},#10
				u'c/c++`c`c++`c语言':{},#9
			},
			u'java':{#6
				u'j2ee':{},#7
				u'java':{},#8
			},
			u'python':{#4
				u'python':{},#5	

			}								
		},
		u'网络`network':{#12

		},
		u'算法`algorithm':{#2

		},
		u'数据结构':{#1

		},
	}
}

class FieldNode(object):
	"""docstring for FieldNode"""
	
	def __init__(self, taglist, level, parents):
		self.tags = [t.lower() for t in taglist.split('`')]
		self.name = self.tags[0]
		self.level   = level
		self.parents = parents
		self.books   = []

	def match(self, tagname):
		if tagname.lower() in self.tags:
			return True

	# a.getBranchLoc(b), return None if a b not in same branch, return 1 if a is one level deeper than b.
	def getBranchLoc(self, node):
		lev = self.level - node.level
		if lev == 0:
			return
		elif lev > 0:
			if node in self.parents:
				return lev 
		else:
			if self in node.parents:
				return lev

class FieldTree(object):
	"""docstring for FieldTree"""

	# fields = {
	# 	u'计算机':{'level':1, 'parents':set(), 'books':[]},
	# 	u'编程':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
	# 	u'C/C++':{'level':4, 'parents':set((u'编程', u'计算机')), 'books':[]},
	# 	u'STL':{'level':4, 'parents':set((u'C/C++', u'编程', u'计算机')), 'books':[]},
	# 	u'java':{'level':4, 'parents':set((u'编程', u'计算机')), 'books':[]},
	# 	u'J2EE':{'level':4, 'parents':set((u'java', u'编程', u'计算机')), 'books':[]},
	# 	u'算法':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
	# 	u'数据结构':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
	# 	u'网络':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
	# }

	field_nodes = []

	def __init__(self, input_tree):
		self.vector = {}
		self.field_nodes = []
		self.parse_fields(input_tree, 1, set(), self.field_nodes)
		# print self.field_nodes

	def parse_fields(self, input_tree, level, parents, output):
		for inp in input_tree.items():
			node = FieldNode(inp[0], level, parents)
			if inp[1]:
				next_parents = set([node])
				next_parents.update(parents)
				self.parse_fields(inp[1], level + 1, next_parents, output)
			output.append(node)

	def getNodeIdx(self, tagname):
		for fn in self.field_nodes:
			if fn.match(tagname):
				return self.field_nodes.index(fn)

	def getNode(self, tagname):
		idx = self.getNodeIdx(tagname)
		if idx is not None:
			return self.field_nodes[idx]

	def getVector(self):
		return self.vector

	def insertBook(self, book):
		lowest_idx = set()
		lowest_lev = 0
		for tag in [t['name'] for t in book['tags']]:
			# if tag not in self.fields:
			# 	continue
			logging.debug('book tag:%s' % tag)
			if tag == u'C++':
				print tag

			## node version
			idx = self.getNodeIdx(tag)
			if idx is None:
				logging.debug('no node book tag %s'%tag)
				continue
			node = self.field_nodes[idx]

			## 获得最低层次node
			if node.level > lowest_lev:
				lowest_lev = node.level
				lowest_idx = set([idx])
			elif node.level == lowest_lev:
				lowest_idx.add(idx)	

			## 累计vector
			if node.name in self.vector:
				self.vector[node.name] += 1
			elif len(self.vector) == 0:
				self.vector[node.name] = 1
				logging.debug(u'获取第一个标签: %s'%tag)
			else:
				_isnewvec = False
				for pre_tag in [x[0] for x in self.vector.items()]:
					pre_node = self.getNode(pre_tag)
					logging.debug('compare node %s and pre_node  %s' % (node.name, pre_node.name))
					ret = node.getBranchLoc(pre_node)
					if not ret:
						logging.debug('node %s not in same branch of pre_node %s' % (node.name, pre_node.name))
						_isnewvec = True
						continue
					if ret > 0:
						logging.debug('get same branch tag: %s, delete old branch tag: %s' % (tag, pre_tag))
						_isnewvec = True
						del self.vector[pre_tag]
					else:
						logging.debug('skip same branch high level tag:%s'%tag)
						_isnewvec = False
						break
					
				if _isnewvec:
					logging.debug('node %s and pre_node %s finally not in same branch' % (node.name, pre_node.name) )
					self.vector[node.name] = 1


		# 分类书籍到节点标签
		for idx in lowest_idx:
			logging.debug('CLASSIFY book:%s TO lowest_idx:%s'% (book['title'], self.field_nodes[idx].name) )
			self.field_nodes[idx].books.append(book)


def main():
	# test FieldTree:
	# test_book = [1767741, 1500149, 1110934, 1091086, 1885170, 1102259, 1230206, 1246192, ]
	# ft = FieldTree(FIELDS)
	# for bk in test_book:
	# 	book = rsdb.findOneBook(unicode(bk))
	# 	if not book or 'tags' not in book:
	# 		continue
	# 	ft.insertBook(book)
	# vec = ft.getVector()

	ft = FieldTree(FIELDS)
	for book in db.books.find(timeout=False):
		if not book or 'tags' not in book:
			continue
		if not book['general_domain'] or book['general_domain'][0][0] != u'技术':
			continue
		ft.insertBook(book)
	vec = ft.getVector()
	logging.debug('=-=-=-Final Vector: %s=-=-=' % (' '.join([ unicode(x[0])+u'='+unicode(x[1]) for x in vec.items() ])))

if __name__ == '__main__':
	main()	