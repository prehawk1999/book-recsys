# -*- coding: utf-8 -*- 
from book_recsys import *
import gensim
from gensim.corpora import textcorpus
import re

if __name__ == '__main__':

    logging.info("running %s" % ' '.join(sys.argv))
 
    # check and process input arguments
    if len(sys.argv) < 2:
        print 'usage: python gen_book_corpus.py <saved_file>'
        sys.exit(1)
    saved_file = sys.argv[1]

    dots = re.compile(ur'[\r\n，。？【】·`]')
    with open(saved_file, 'w') as f: 
        for b in db.books.find():
            if 'summary' in b and b['summary'].strip():
                smry = re.sub(dots, "", b['summary'])
                wstr = '%s\r' % (b['summary'])
                f.write(wstr.encode('utf-8'))
            if 'author_intro' in b and b['author_intro'].strip():
                ath_intr = re.sub(dots, "", b['author_intro'])
                wstr = '%s\r' % (b['author_intro'])
                f.write(wstr.encode('utf-8'))