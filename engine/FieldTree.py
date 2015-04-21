# -*- coding: utf-8 -*- 
from book_recsys import *


FIELDS = {
	u'计算机`计算机科学`计算机技术':{ # 1
		u'程序设计`编程`程序开发`编程语言`programming':{
			u'C`C++`C/C++`c语言':{
				u'stl':{},
			},
			u'java':{
				u'J2EE':{},

			},
			u'':{

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
		u'C/C++':{'level':3, 'parents':set((u'编程', u'计算机')), 'books':[]},
		u'stl':{'level':4, 'parents':set((u'C/C++', u'编程', u'计算机')), 'books':[]},
		u'java':{'level':3, 'parents':set((u'编程', u'计算机')), 'books':[]},
		u'J2EE':{'level':4, 'parents':set((u'java', u'编程', u'计算机')), 'books':[]},
		u'算法':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
		u'数据结构':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
		u'网络':{'level':2, 'parents':set((u'计算机',)), 'books':[]},
	}

	def __init__(self):
		self.vector = {}

	# def build_fields():

	# 	FieldTree.fields = 

	def _getLevel(self, tagname):
		if tagname not in FieldTree.fields:
			return 
		return FieldTree.fields[tagname]['level']

	# return None if a and b not in a branch, 1 if a is lower, -1 if b is lower.
	def _getBranchLoc(self, a, b):
		if a not in FieldTree.fields or b not in FieldTree.fields:
			return 
		alev = self._getLevel(a)
		blev = self._getLevel(b)
		if alev == blev:
			return
		elif alev > blev:
			if b in FieldTree.fields[a]['parents']:
				return 1
		else:
			if a in FieldTree.fields[b]['parents']:
				return -1

	def getResultVector(self):
		return self.vector

	def insertBook(self, book):
		lowest_tag = []
		lowest_lev = 0
		for tag in [t['name'] for t in book['tags']]:
			if tag not in FieldTree.fields:
				continue

			# 获得最低层次
			tag_lev = FieldTree.fields[tag]['level']
			if tag_lev > lowest_lev:
				lowest_lev = tag_lev
				lowest_tag = [tag]
			elif tag_lev == lowest_lev:
				lowest_tag.append(tag)
			
			# 累加vector
			if tag in self.vector:
				self.vector[tag] += 1
			elif len(self.vector) == 0:
				self.vector[tag] = 1
				logging.debug('get first tag: %s'%tag)
			else:
				_isnewtag = False
				for pre_tag in self.vector.items():
					ret = self._getBranchLoc(tag, pre_tag[0])
					logging.debug('-=- compare tag:%s and pre_tag:%s' %(tag, pre_tag[0]))
					if not ret:
						_isnewtag = True
						continue
					if ret > 0:
						_isnewtag = True
						del self.vector[pre_tag[0]]
						logging.debug('get same branch tag: %s, delete old branch tag: %s' % (tag, pre_tag[0]))
					else:
						_isnewtag = False
						logging.debug('skip same branch high level tag:%s'%tag)
				if _isnewtag:
					self.vector[tag] = 1


		# 分类书籍到节点标签
		for tag in lowest_tag:
			logging.debug('CLASSIFY book:%s TO lowest_tag:%s'% (book['title'], tag) )
			FieldTree.fields[tag]['books'].append(book)

def main():
	# test FieldTree:
	test_book = [1767741, 1500149, 1110934, 1091086, 1885170, 1102259, 1230206, 1246192, ]
	ft = FieldTree()
	for bk in test_book:
		book = rsdb.findOneBook(unicode(bk))
		if not book or 'tags' not in book:
			continue
		# print book['title']
		ft.insertBook(book)
	vec = ft.getResultVector()
	logging.debug('=-=-=-Final Vector: %s=-=-=' % (' '.join([ unicode(x[0])+u'='+unicode(x[1]) for x in vec.items() ])))

if __name__ == '__main__':
	main()	