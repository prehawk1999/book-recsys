# -*- coding: utf-8 -*- 
from book_recsys import *


class KNN:

	def __init__(self, mtrx):
		self.mtrx = mtrx

	# {'cls1':[tag1,tag2], 'cls2':[tag3,tag4]}
	def setInitClass(self, train_class):
		for cl in train_class.values():
			for c in cl:
				if c not in self.mtrx:
					return False
		self.train_class = train_class
		self.test_class  = dict([(x,[]) for x in train_class.keys()])
		return True

	def getCluster(self, K):
		for vec in self.mtrx.items():
			for cl in self.train_class.keys():



def main():
	pass

if __name__ == '__main__':
	main()