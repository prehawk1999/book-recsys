# -*- coding: utf-8 -*- 
from book_recsys import *


FIELDS = {
	u'计算机`计算机科学`计算机技术':{ # 1
		u'程序设计`编程`程序开发`编程语言`programming':{
			u'c`c++`c/c++`c语言':{
				u'stl':{},
				u'c`c++`c/c++`c语言':{},
			},
			u'java':{
				u'j2ee':{},
				u'java':{},
			},
			u'python':{
				u'python':{},

			}								
		},
		u'网络':{

		},
		u'算法':{

		},
		u'数据结构':{

		},
	}
}


class FieldTree(object):
	"""docstring for FieldTree"""

	fields = {
		u'计算机':{'level':1, 'parents':set(), 'books':[]},
		u'编程':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
		u'C/C++':{'level':4, 'parents':set((u'编程', u'计算机')), 'books':[]},
		u'STL':{'level':4, 'parents':set((u'C/C++', u'编程', u'计算机')), 'books':[]},
		u'java':{'level':4, 'parents':set((u'编程', u'计算机')), 'books':[]},
		u'J2EE':{'level':4, 'parents':set((u'java', u'编程', u'计算机')), 'books':[]},
		u'算法':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
		u'数据结构':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
		u'网络':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
	}

	field_nodes = []

	def __init__(self, input_tree):
		self.vector = {}

	def getNodeIdx(self, tagname):
		for fn in self.field_nodes:
			if fn.match(tagname):
				return field_nodes.index(fn)

	def _getLevel(self, tagname):
		if tagname not in FieldTree.fields:
			return 
		return FieldTree.fields[tagname]['level']

	# return None if a and b not in a branch, 1 if a is 1level lower than b, -1 if b is 1level lower than a.
	def _getBranchLoc(self, a, b):
		if a not in FieldTree.fields or b not in FieldTree.fields:
			return 
		alev = self._getLevel(a)
		blev = self._getLevel(b)
		if alev == blev:
			return
		elif alev > blev:
			if b in FieldTree.fields[a]['parents']:
				return alev - blev
		else:
			if a in FieldTree.fields[b]['parents']:
				return alev - blev

	def getVector(self):
		return self.vector

	def insertBook(self, book):
		lowest_node = []
		lowest_lev = 0
		for tag in [t['name'] for t in book['tags']]:
			if tag not in FieldTree.fields:
				continue
			logging.debug('book tag:%s' % tag)
			# idx = self.getNodeIdx(tag)
			# if not idx:
			# 	continue
			# node = self.field_nodes[idx]

			## 获得最低层次node
			# if node.level > lowest_lev:
			# 	lowest_lev = nodel.level
			# 	lowest_idx = [idx]
			# elif node.level == lowest_lev:
			# 	lowest_tag.append(idx)	

			## 获得最低层次
			tag_lev = FieldTree.fields[tag]['level']
			if tag_lev > lowest_lev:
				lowest_lev = tag_lev
				lowest_tag = [tag]
			elif tag_lev == lowest_lev:
				lowest_tag.append(tag)
			
			## 累加vector
			if tag in self.vector:
				self.vector[tag] += 1
			elif len(self.vector) == 0:
				self.vector[tag] = 1
				logging.debug(u'获取第一个标签: %s'%tag)
			else:
				_isnewvec = False
				for pre_tag in self.vector.items():
					ret = self._getBranchLoc(tag, pre_tag[0])
					logging.debug('-=- compare tag:%s and pre_tag:%s' % (tag, pre_tag[0]))
					if not ret:
						_isnewvec = True
						continue
					if ret > 0:
						_isnewvec = True
						del self.vector[pre_tag[0]]
						logging.debug('get same branch tag: %s, delete old branch tag: %s' % (tag, pre_tag[0]))
					else:
						_isnewvec = False
						logging.debug('skip same branch high level tag:%s'%tag)
				if _isnewvec:
					self.vector[tag] = 1


		# 分类书籍到节点标签
		for tag in lowest_tag:
			logging.debug('CLASSIFY book:%s TO lowest_tag:%s'% (book['title'], tag) )
			FieldTree.fields[tag]['books'].append(book)

class FieldNode(object):
	"""docstring for FieldNode"""
	
	def __init__(self, taglist):
		self.tags = [t.lower() for t in taglist.split('`')]
		self.name = self.tags[0]
		self.level   = 0
		self.parents = set()
		self.books   = []

	def match(self, tagname):
		if tagname.lower() in self.tags:
			return True

	def isParenting(self, node):
		pass

	# a.getBranchLoc(b), return None if a b not in same branch, return 1 if a is one level deeper than b.
	def getBranchLoc(self, node):
		lev = self.level - node.level
		if lev > 0:
			if not node.isParenting(self):
				return
			else:
				return lev 
		else:
			if not self.isParenting(node):
				return
			else:
				return lev

def main():
	# test FieldTree:
	test_book = [1767741, 1500149, 1110934, 1091086, 1885170, 1102259, 1230206, 1246192, ]
	ft = FieldTree(FIELDS)
	for bk in test_book:
		book = rsdb.findOneBook(unicode(bk))
		if not book or 'tags' not in book:
			continue
		# print book['title']
		ft.insertBook(book)
	vec = ft.getVector()
	logging.debug('=-=-=-Final Vector: %s=-=-=' % (' '.join([ unicode(x[0])+u'='+unicode(x[1]) for x in vec.items() ])))

if __name__ == '__main__':
	main()	