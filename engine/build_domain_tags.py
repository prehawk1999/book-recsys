# -*- coding: utf-8 -*- 
from book_recsys import *
from stdtag import StandardTags
from wac import *
import gensim

stdtag = StandardTags()
stdtag._loadStart()

INP_DOM = u'计算机'

def main():
	model = gensim.models.Word2Vec.load("corpus/misc.model")
	tags = []
	for tag in stdtag.start:
		try:
			sim = model.similarity(tag, INP_DOM)
		except:
			continue
		tags.append( (tag, sim) )
	tags.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse=True)

	with open('log/tag.domain.txt', 'w') as f:
		for t in tags:
			pstr = '%s %f\n' % (t[0], t[1])
			f.write(pstr.encode('utf-8'))

if __name__ == '__main__':
	main()
