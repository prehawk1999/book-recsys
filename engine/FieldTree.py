# -*- coding: utf-8 -*- 
from book_recsys import *

class FieldTree(object):
	"""docstring for FieldTree"""

	fields = {u'':{'level':1, 'parents':set(), 'books':[]}}

	def __init__(self, arg):
		self.vector = {}

	def _getLevel(self, tagname):
		if tagname not in FieldTree.fields:
			return 
		return FieldTree.fields[tagname]['level']

	# return None if a and b not in a branch, 1 if a is lower, -1 if b is lower.
	def _getBranchLoc(self, a, b):
		if a not in FieldTree.fields or b not in FieldTree.fields:
			return 
		alev = _getLevel(a)
		blev = _getLevel(b)
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
			else:
				for pre_tag in self.vector.items():
					ret = _getBranchLoc(tag, pre_tag)
					if not ret:
						self.vector[tag] = 1
						break
					if ret > 0:
						self.vector[tag] = 1
						del self.vector[pre_tag]

		# 分类书籍到节点标签
		for tag in lowest_tag:
			FieldTree.fields[tag]['books'].append(book)

def main():
	# test FieldTree:
	ft = FieldTree()
	for bk in test_book:
		book = rsdb.findOneBook(bk)
		if not book or 'tags' not in book:
			continue
		ft.insertBook(book)
	vec = ft.getResultVector()
	print vec

if __name__ == '__main__':
	main()	