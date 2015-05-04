# -*- coding: utf-8 -*- 
from book_recsys import *
from FieldTree import *

def getProEval(vec):
    ret = 0.0
    for i in vec.values():
        ret += i
    return ret

def test_interest_recbooks(u):
    for i in u['interest_recbooks']:
        print '=%s=%r, %r'%('-'*5,i[0],i[1])
        for j in i[1]:
            print j[1]
    # interest_eval_sort = u['interest_eval'].items()
    # interest_eval_sort.sort(cmp=lambda a,b:cmp(a[1], b[1]), reverse=True)
    # for i in interest_eval_sort:
    #   # print '%s'%('-'*5,i[2])
    #   print i[0], i[1]

def test_field_recbooks(u):
    for i in u['field_recbooks'].items():
        print '=%s=%s'%('-'*5,i[0])
        print '\r\n'.join([x[1] for x in i[1]]) 

def test_field():
    for fd in db.fields.find():
        print '=%s=%s' % ('-'*10, fd['field'])
        for book in fd['books']:
            print '=%s=%s' % ('-'*3, book['title'])


def main():
    # umodels = {}
    # for u in db.umodel.find(timeout=False):
    #   print '=%s=%s' % ('-'*10,u['user_id'])
    #   test_field_recbooks(u)
    #   # test_interest_recbooks(u)
    
    test_field()


if __name__ == '__main__':
    main()