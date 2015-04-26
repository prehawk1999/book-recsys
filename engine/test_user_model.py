# -*- coding: utf-8 -*- 
from book_recsys import *


def getProEval(vec):
	ret = 0.0
	for i in vec.values():
		ret += i
	return ret


def main():
	pass
	umodels = {}
	for u in db.umodel.find(timeout=False):
		print '=%s=%s' % ('-'*10,u['user_id'])
		for i in u['field_recbooks'].items():
			print '=%s=%s'%('-'*5,i[0])
			for j in i[1]:
				print j[1]


if __name__ == '__main__':
	main()