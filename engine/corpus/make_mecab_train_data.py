#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: 52nlpcn@gmail.com
# Copyright 2015 @ YuZhen Technology

import codecs
import sys

def make_mecab_train_data(input_file, output_file):
    input_data = codecs.open(input_file, 'r', 'utf-8')
    output_data = codecs.open(output_file, 'w', 'utf-8')
    for line in input_data.readlines():
        word_list = line.strip().split()
        if len(word_list) == 0: continue
        for word in word_list:
            output_data.write(word+ "\t0,0,0,0,0,0\n")
        output_data.write("EOS\n")
    input_data.close()
    output_data.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "pls use: python make_mecab_train_data.py input output"
        sys.exit()
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    make_mecab_train_data(input_file, output_file)