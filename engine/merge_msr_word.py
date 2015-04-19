# -*- coding: utf-8 -*- 
from book_recsys import *


def main(inp1, inp2):
	msrreader = csv.reader(open(inp1))
	words = set()
	for row in msrreader:
		words.add(row[0].strip().decode('utf-8'))
	for tag in open(inp2):
		words.add(tag.strip().decode('utf-8'))
	writer = csv.writer(open(inp1, 'w'))
	for w in words:
		writer.writerow([w.encode('utf-8'),0,0,0,0,0,0])
    


if __name__ == '__main__':
    logging.info("running %s" % ' '.join(sys.argv))
 
    # check and process input arguments
    if len(sys.argv) < 3:
        print 'usage: python merge_msr_word.py <msr_words.csv> <tags.standard.txt>'
        sys.exit(1)
    inp1, inp2 = sys.argv[1:]
    main(inp1, inp2)