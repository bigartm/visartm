# -*- coding: utf-8 -*-
import numpy as np 
import json 
import algo.arranging.base as arr
import algo.metrics as metrics

model = research.model
topics = model.get_topics()

N = len(topics)
try:
	if research.problem.model != research.model:
		raise ValueError("Model differs from the assessed one!")
	C = np.array(research.problem.get_results())
except:
	C = np.zeros((N, N))

	

research.report("Темы:")
research.report_table([[str(topic.index_id), topic.title] for topic in topics])
	
research.report("Оценки:")
research.report_table(C)


research.report("Ближашие три темы по мнению пользователей:")
for i in range(N):
	research.report(str(topics[i]))
	#print(list(np.argsort(C[i])))
	for jj in np.argsort(-C[i])[0:3]:
		j = int(jj)
		research.report_html("&nbsp; &nbsp; &nbsp; &nbsp;  %s (%f)<br>" % (str(topics[j]), C[i][j] ))


	
modes = ["none", "hamilton", "tsne", "mds", "dendro"] 
mode_names = {
	"none" : "No arranging",
	"hamilton" : "LKH",
	"tsne" : "t-SNE",
	"mds" : "MDS",
	"dendro" : "Agl. Clust."
}

 
answers = [["Метрика", "Алгоритм", "NDS", "CANR", "OANC", "TONC", "NRN", "ANRA", "UP", "UMC"]]
answers_lkh = [["Метрика", "CANR", "TONC",  "ANRA", "UP", "UMC", "NRN"]]
for metric in metrics.metrics_list:	
	dist =	model.get_topics_distances(metric=metric)	
	research.report_html("<h2>Метрика %s</h2>" % metric)
	research.show_matrix(dist)
	
	
	for mode in modes:
		perm = arr.get_arrangement_permutation(dist, mode)
		answers.append([
			(metric if mode == "none" else ""), 
			mode_names[mode], 
			"%.04f" % arr.NDS(dist, perm),
			"%.04f" % arr.CANR(dist, perm),
			"%.06f" % arr.OANC(dist, perm),
			"%.04f" % arr.TONC(dist, perm),
			"%.02f" % arr.NRN(C, perm),
			"%.02f" % arr.ANRA(C, perm),
			"%.02f" % arr.UP(C, perm),
			("%.04f" % arr.UMC(C, dist) if mode=="none" else "")
		])
		
		if mode == "hamilton":
			answers_lkh.append([metric,
				"%.04f" % arr.CANR(dist, perm),
				"%.04f" % arr.TONC(dist, perm),
				"%.04f" % arr.ANRA(C, perm),
				"%.02f" % arr.UP(C, perm),
				"%.04f" % arr.UMC(C, dist),
				"%.02f" % arr.NRN(C, perm)
			])
		
		if mode == "hamilton":
			DDC = arr.DDC(dist, perm)
			CDC = arr.CDC(dist, perm)
			
			
			fig = research.get_figure(figsize=(10,10))
		 
			ax1 = fig.add_subplot(211)
			ax1.set_xlabel("d", fontsize=20)
			ax1.set_ylabel("CDC", fontsize=20)
			ax1.plot(range(1,N-1), CDC[0:N-2])
			
			ax2 = fig.add_subplot(212)
			ax2.set_xlabel("d", fontsize=20)
			ax2.set_ylabel("DDC", fontsize=20)
			ax2.plot(range(1,N-1), DDC[0:N-2])

			research.report_picture(width=400)
			
research.report_table(answers)
research.report_table(answers_lkh)
