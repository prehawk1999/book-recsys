# -*- coding: utf-8 -*- 
from book_recsys import *


def getProEval(vec):
	ret = 0.0
	for i in vec.values():
		ret += i
	return ret


def main():
	umodels = {}
	for u in db.umodel.find(timeout=False):
		print '=%s=%s' % ('-'*10,u['user_id'])
		# for i in u['field_recbooks'].items():
		# 	print '=%s=%s'%('-'*5,i[0])
		# 	for j in i[1]:
		# 		print j[1]
		interest_eval_sort = u['interest_eval'].items()
		interest_eval_sort.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
		for i in interest_eval_sort:
			# print '%s'%('-'*5,i[2])
			print i[0], i[1]





if __name__ == '__main__':
	main()