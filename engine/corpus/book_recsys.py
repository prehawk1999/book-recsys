# -*- coding: utf-8 -*- 

import math
import numpy
import os,sys
import csv
import datetime
import logging
import pickle
from time import sleep  
import pymongo
from pymongo import MongoClient

# mongo数据库配置
conn = MongoClient('localhost',27017) 
db = conn.group_mems

# 日志模块配置
logging.basicConfig(level=logging.DEBUG,
                format='[%(asctime)s | %(funcName)s]: %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='Analysis.log',
                filemode='a')

console = logging.StreamHandler()

formatter = logging.Formatter('[%(asctime)s | %(funcName)s]: %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

PROG       = 100
PROG_REC   = 0 
PROG_SCALE = (0,10,20,30,40,50,60,70,80,90,100)

# set PROG before using this function
def prog_d(dstr, line=-1, total=100):
    global PROG_REC
    if line >= 0:
        progress = int(float(line)/float(total) * 100 + 1)
        if progress not in PROG_SCALE or progress == PROG_REC:
            return
        PROG_REC = progress
        dstr += ' %d%%(%d/%d) -=-=-' % (progress, line, total)
        logging.debug('-=-=- Processing ' + dstr)
    else:
        logging.debug('-=-=- Finishing ' + dstr)


def getLines(inpfile):
    count = -1
    for count,line in enumerate(open(inpfile,'rU')):  
        pass      
    count += 1
    return count