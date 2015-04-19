# -*- coding: utf-8 -*- 
from book_recsys import *
from wac import loadLevel


def main(thres=0.00001):
    level = loadLevel()
    levnodes = level[0][2].keys()
    assoStren = dict([(x, []) for x in level[0][2].keys()]) # 启动标签 
    for asso in assoStren.keys(): # 每个启动标签
        for lev in range(len(level)): # 每一层
            # 构造一层与当前节点相关的关联强度
            assoPend = dict([(x, 0.0) for x in level[lev][2].keys()])
            if lev == 0:
                # 第一层只标记0或者1
                for tag in level[lev][2].keys(): # 每一层里的每个标签
                    if asso == tag:
                        assoPend[tag] = 1.0
                    else:
                        assoPend[tag] = 0.0
            else:
                for tag in level[lev][2].keys(): 
                    # 使用前一层的标签计算与当前层tag的P值以及其关联强度的乘积
                    for pre_tag in level[lev-1][2].items(): # 前一层的标签 pre_tag[0] unicode, pre_tag[1] dict
                        assoPend[tag] += assoStren[asso][lev-1][pre_tag[0]] * pre_tag[1][tag]# AS * P

            # 添加一层关联强度
            assoStren[asso].append(assoPend)
    pickle.dump(assoStren, open('dump/assostren.dmp', 'w') )



if __name__ == '__main__':
	main()