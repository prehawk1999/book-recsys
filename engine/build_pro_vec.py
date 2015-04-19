# -*- coding: utf-8 -*- 
from book_recsys import *
# from stdtag import StandardTags
from wac import *
import gensim

# stdtag = StandardTags()
stdtag._loadStart()
stdtag._loadDomain()
#level = loadLevel()

### 人工分类的领域，需要转换为顶层标签对应领域
# domain = {
# 	u'技术' : [u'统计学', u'设计模式', u'技术分析', u'生物学', u'计算机科学', u'计算机技术'],
# 	u'经济' : [u'经济学', u'经济管理'],
# 	u'文学' : [u'诗歌', u'红学', u'职场小说', u'古代文学', u'俄国文学', u'午夜文库', u'散文', u'德语文学'],
# 	u'艺术' : [u'绘画', u'艺术', u'美学'] ,
# 	u'历史' : [u'清史', u'传记'],
# 	u'文化' : [u'语文', u'西方', u'中国文化', u'经学', u'新媒体', u'欧美', u'文化研究' ],
# 	u'金融' : [u'金融学'],
# 	u'漫画' : [u'漫画'],
# 	u'法学' : [u'法学'],
# }

domain = {
	u'程序设计' : [u'程序设计', u'调试', u'并发', u'版本控制', u'程序开发', u'前端开发', u'移动开发', u'多线程', u'云计算', u'编译原理', u'算法'],
	u'信息安全' : [u'信息安全', u'计算机安全', u'加密解密', u'密码学'],
	u'人工智能' : [u'人工智能', u'人机交互', u'机器学习', u'推荐系统'],
	u'集体智慧' : [u'集体智慧', u'数据分析', u'回归分析', u'数值分析'],
	u'计算机硬件' : [u'单片机', u'嵌入式', u'硬件编程', u'嵌入式系统'],
	u'计算机网络' : [u'计算机网络', u'网络协议', u'网络编程'],
	u'计算机图像' : [u'计算机图像', u'机器视觉', u'数字图像处理', u'计算机视觉'],
}

ASSO_THRES = 0.0
WORD2VEC_THRES = 0.0

def build_provec():

	### 获得顶层标签的领域对应, 第四层
	toptag = {}
	for d in domain.items():
		for tag in d[1]:
			toptag[tag] = d[0]

	### 根据关联强度对每个顶层标签聚类所有启动标签，按照关联强度排列
	assostren = pickle.load(open('dump/assostren.dmp'))
	
	# 获得顶层标签对于启动标签的关联强度
	toptag_cluster = {}
	for tag in toptag.keys():
		cluster = []
		for sttag in assostren.keys():
			# print sttag
			if tag not in assostren[sttag][4]:
				continue
			assoval =  assostren[sttag][4][tag]
			#logging.debug('assoval %f' % assoval)
			
			if assoval > ASSO_THRES:
				cluster.append( (sttag, assoval) )
			# print len(cluster)

		cluster.sort( cmp=lambda a,b:cmp(a[1], b[1]), reverse=True )
		# for t in cluster:
		logging.debug('toptag_cluster: %s - [%s]\r\n\r\n' % (tag, ' '.join([x[0] for x in cluster]) ))
		toptag_cluster[tag] = cluster

	pickle.dump(toptag_cluster, open('dump/toptagcluster.dmp', 'w'))

	### 构建pro_vec，完成Step1
	logging.debug(u'构建pro_vec，完成Step1')
	pro_vec = {}
	for sttag in assostren.keys(): # 启动标签
		idxmin = 1000
		ttag_spec = ''
		for ttag in toptag_cluster.items(): # 顶层标签
			cluster = [x[0] for x in ttag[1]]
			if sttag not in cluster:
				continue
			idx = cluster.index(sttag)
			if idx < idxmin:
				idxmin = idx
				ttag_spec = ttag[0]
		if not ttag_spec:
			continue
		pro_vec[sttag] = ( ttag_spec, math.log(idxmin + 2))
		logging.debug('%s, %s, %f' % (sttag, ttag_spec, math.log(idxmin + 2)) )
	pickle.dump(pro_vec, open('dump/provec.dmp', 'w'))
	# return assostren, toptag_cluster
		
def build_provec_v2():
	### 获得顶层标签的领域对应, wac树的其中一层
	logging.debug(u'获得顶层标签的领域对应, 第四层')
	toptag = {}
	for d in domain.items():
		for tag in d[1]:
			toptag[tag] = d[0]

	### 根据关联强度对每个顶层标签聚类所有启动标签，按照关联强度排列
	# logging.debug(u'根据关联强度对每个顶层标签聚类所有启动标签，按照关联强度排列')
	# assostren = pickle.load(open('dump/assostren.dmp'))
	toptag_cluster = {}

	### 尝试用word2vec来聚类
	model = gensim.models.Word2Vec.load("corpus/misc.model")

	# 获得每个领域标签的启动标签聚类
	toptag_cluster = {}
	for t1 in toptag.keys():
		cluster = []
		for t2 in stdtag.domain:
			sim = similar(t1, t2, model)
			if sim > WORD2VEC_THRES:
				cluster.append( (t2, sim) )
			# print t1, t2, similar(t1, t2, model)
			# logging.info('toptag: %s, starttag: %s - %f' % (t1, t2, similar(t1, t2) ) )
		cluster.sort( cmp=lambda a,b:cmp(a[1], b[1]), reverse=True )
		toptag_cluster[t1] = cluster
		logging.debug('toptag: %s, starttag [%s]' % (t1, ' '.join([unicode(x[0])+unicode(x[1]) for x in cluster]) ) )

	# pickle.dump(toptag_cluster, open('dump/toptagcluster.dmp', 'w'))
	
	logging.debug(u'构建pro_vec，完成Step1')
	pro_vec = {}
	for sttag in stdtag.domain: # 启动标签
		idxmin = 1000
		simmin = 0
		ttag_spec = ''
		for ttag in toptag_cluster.items(): # 顶层标签
			cluster = [x[0] for x in ttag[1]]
			if sttag not in cluster:
				continue
			idx = cluster.index(sttag)
			sim = ttag[1][idx][1]
			print sim
			if sim > simmin:
				simmin = sim
				ttag_spec = ttag[0]
		if not ttag_spec:
			continue
		pro_vec[sttag] = ( ttag_spec, math.log(simmin + 2) )
		logging.debug(u'%s - %s, %f' % (sttag, ttag_spec, math.log(simmin + 2)) )
	pickle.dump(pro_vec, open('dump/provec.dmp', 'w'))

def similar(a, b, model):
	try:
		return model.similarity(a, b)
	except:
		return 0.0


if __name__ == '__main__':
	build_provec_v2()
