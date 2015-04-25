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


	# 	umodels[u['user_id']] = u

	# umodel_show = umodels.items()
	# umodel_show.sort(cmp=lambda a,b:cmp(getProEval(a['pro_eval']), getProEval(b['pro_eval'])), reverse=True)
	# for um in umodel_show:
	# 	print um['user_id'], getProEval(um['pro_eval']), ' '.join([ unicode(x[0])+unicode(x[1])+u' ' for x in um['pro_eval'] ])

	

if __name__ == '__main__':
	main()