# -*- coding: utf-8 -*- 
from book_recsys import *
import jieba

if __name__ == '__main__':
    logging.info("running %s" % ' '.join(sys.argv))
 
    # check and process input arguments
    if len(sys.argv) < 3:
        print 'usage: python jieba_cut.py <inputfile> <outputfile> [<userdict>]'
        sys.exit(1)

    if len(sys.argv) == 4:
        inp1, outp, inp2 = sys.argv[1:]
        jieba.load_userdict(inp2)
        prog_d('jieba userdict loaded: %s' % inp2)
    elif len(sys.argv) == 3:
        inp1, outp = sys.argv[1:]

    totallines = getLines(inp1)
    with open(outp, 'w+') as jiebaf:
        with open(inp1) as srcf:
            for i,line in enumerate(srcf):
                jiebaf.write(' '.join(list(jieba.cut(line.decode('utf-8')))).encode('utf-8') )
                prog_d('jieba write lines', i, totallines)