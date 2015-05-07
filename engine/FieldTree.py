# -*- coding: utf-8 -*- 
from book_recsys import *

FIELDS = {
	u'计算机`计算机科学`计算机技术':{ # 0
		u'软件`程序设计`编程`程序开发`programming':{#3
			u'编程语言':{
				u'c/c++`c`c++`c语言':{#9
					u'stl':{},#10
					u'c/c++`c`c++`c语言':{},#11
				},
				u'java':{#6
					u'j2ee':{},#7
					u'java':{},#8
				},
				u'python':{},
				u'动态语言':{},
				u'汇编语言':{}
			},
			u'软件测试':{},
			u'游戏编程':{},
			u'嵌入式':{},
			u'设计模式':{},
			u'手机开发':{},
			u'版本控制':{}
		},
		u'网络`network`计算机网络':{#12

		},
		u'算法与数据结构`数据结构与算法':{
			u'算法`algorithm':{},
			u'数据结构`datastructure':{},		
		},
		u'信息安全`计算机安全`网络安全':{
			u'密码学':{}
		},
		u'人工智能':{
			u'自然语言处理`计算语言学':{
				u'语料库':{},
				u'生成语言学':{},
				u'话语分析':{}
			},
			u'神经网络':{},
			u'遗传算法':{},
			u'推荐系统':{},
			u'机器学习':{},
			u'人工智能':{}
		},
		u'大数据`云计算`数据':{
			u'数据挖掘':{},
			u'数据可视化':{},
			u'数据仓库':{}
		}
	}
}

class FieldNode(object):
	"""docstring for FieldNode"""
	
	def __init__(self, taglist, level, parents):
		self.tags = [t.lower() for t in taglist.split('`') if t]
		self.name = self.tags[0]
		self.level   = level
		self.parents = parents
		self.books   = []
		self.books_allow  = set()
		self.books_exists = set()

	def match(self, tagname):
		if tagname.lower() in self.tags:
			return True

	def multi_match(self, tags):
		for t in tags:
			if t.lower() in self.tags:
				return True

	def insertBook(self, book):
		# print book['id'] in self.books_allow, len(self.books_allow), self.books_allow
		if 'id' in book and book['id'] not in self.books_exists and book['id'] in self.books_allow:
			self.books.append(book)
			self.books_exists.add(book['id'])
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

	field_nodes = []
	mem = set()

	def __init__(self, input_tree=FIELDS, tree_dump='dump/FieldTreeNodes.dmp'):
		self.vector = {}
		if not FieldTree.field_nodes:
			if isinstance(FIELDS, dict):
				self._parse_fields(input_tree, 1, set(), FieldTree.field_nodes)
				logging.debug('INITIALIZE field_nodes: %d' % len(FieldTree.field_nodes))
			elif isinstance(FIELDS, list):
				FieldTree.field_nodes = FIELDS

	def _parse_fields(self, input_tree, level, parents, output):
		for inp in input_tree.items():
			node = FieldNode(inp[0], level, parents)
			output.append(node)
			if inp[1]:
				parents_set = set([node])
				parents_set.update(parents)
				self._parse_fields(inp[1], level + 1, parents_set, output)

	def _getNodeIdx(self, tagname):
		for fn in FieldTree.field_nodes:
			if fn.match(tagname):
				return FieldTree.field_nodes.index(fn)

	def _getNode(self, tagname):
		idx = self._getNodeIdx(tagname)
		if idx is not None:
			return FieldTree.field_nodes[idx]


	def getVector(self):
		return self.vector

	def insertBook(self, book):
		lowest_idx = set()
		lowest_lev = 0
		tags = [t['name'] for t in book['tags']]
		for tag in tags:

			idx = self._getNodeIdx(tag)
			if idx is None:
				continue
			node = FieldTree.field_nodes[idx]

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
					pre_node = self._getNode(pre_tag)
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
			logging.debug('CLASSIFY book:%s TO lowest_idx:%s'% (book['title'], FieldTree.field_nodes[idx].name) )
			FieldTree.field_nodes[idx].books_allow.add(book['id'])

def main():
	# test FieldTree:
	test_book = [1767741, 1500149, 1110934, 1091086, 1885170, 1102259, 1230206, 1246192, ]
	# 
	ft = FieldTree(FIELDS)
	for book in db.books.find(timeout=False):
		# book = rsdb.findOneBook(unicode(bk))
		if not book or 'tags' not in book:
			continue
		ft.insertBook(book)
	vec = ft.getVector()
	for fn in ft.field_nodes:
		logging.info('node: %s, level:%d' % (fn.name, fn.level) )
	logging.info('=-=-=-Final Vector: %s=-=-=' % (' '.join([ unicode(x[0])+u'='+unicode(x[1]) for x in vec.items() ])))

if __name__ == '__main__':
	main()	