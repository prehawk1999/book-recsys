# -*- coding: utf-8 -*- 
from book_recsys import *
from wac import getWacWeight, loadLevel, print_wac #getWordWeight
import gensim


model = gensim.models.Word2Vec.load("corpus/misc.model")
# stdtag = StandardTags()
# level = loadLevel()

THRES = 4.0

def similar(a, b):
	try:
		return model.similarity(a, b)
	except:
		return 0.0

def getBookDomain(book, domainlst):
	weight = dict([(x,0.0) for x in domainlst])

	for i,tag in enumerate(book['tags']):
		tag = stdtag.simple_transform(tag['name'])
		if not tag:
			continue
		for d in domainlst:
			sim = similar(tag, d)
			weight[d] += sim 
			# weight[d] += similar(book['title'], d)
			#logging.debug('book %s tag %s sim %f domain %s' % (book['title'], tag, sim, d))
		# prog_d('tag %s' % tag, i, 8)
		#logging.debug('tag %s' % tag)
	weightI = weight.items()
	weightI.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse=True)
	return weightI[:2]

def build_book_domain(domain):

	for i,book in enumerate( db.books.find(timeout=False) ): # {"$where":"this.domain == null"}, 
		if 'title' not in book:#  or int(book['id']) not in [3609132, 3412260, 1082154, 1012032, 1012379]:
			continue
		w = getBookDomain(book, domain)
		if w and float(w[0][1]) > float(THRES):
			book['general_domain'] = w
			logging.debug('%d building book %s in domain %s - %f, %s - %f' % (i, book['title'], w[0][0], w[0][1], w[1][0], w[1][1]) )
		else:
			book['general_domain'] = []
			logging.debug('book %s has no general_domain' % book['title'])
		ret = db.books.update({"_id":book['_id']}, book)
		if not ret['ok']:
			logging.warn('update book %s error.' % book['title'])

def main():
	build_book_domain(BOOK_DOMAIN)

if __name__ == '__main__':
	main()