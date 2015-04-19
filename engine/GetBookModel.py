# -*- coding: utf-8 -*- 
from book_recsys import *
from GetWacWeight import getWacWeight, loadLevel, print_wac

level = loadLevel()


def getBookModel(book, thres=0, iter_level=10):
	ret = {}
	print '\r\n'*5
	print '='*10, book['title'], '='*10
	for tag in [x['name'] for x in book['tags']]:
		tag_level = getWacWeight(tag, level, iter_level)
		if not tag_level:
			continue
		for lev_tag in tag_level.items():
			idf = db.tags.find_one({"name":lev_tag[0]},{"idf":1})['idf']
			weight = float(idf)*float(lev_tag[1])
			if lev_tag[0] not in ret:
				ret[lev_tag[0]] = 0.0
			ret[lev_tag[0]] += weight
	ret_list = [x for x in ret.items() if x[1] > thres]
	ret_list.sort(cmp=lambda a,b: cmp(a[1],b[1]), reverse=True)
	for i in ret_list:
		print i[0], i[1]
	return dict(ret_list)
			
			

def test_book_model():
	test_book = [3259440, 25708312, 1090601, 5939753, 1767741]

	for bid in test_book:
		book = db.books.find_one({"id":bid})
		if not book:
			continue
		tag_list = getBookModel(book, -10, 0)
	prog_d('test_book_model')

if __name__ == '__main__':
	test_book_model()