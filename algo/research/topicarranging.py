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
	
modes = ["hamilton", "tsne", "mds", "dendro"] 
mode_names = {
	"hamilton" : "LKH",
	"tsne" : "t-SNE",
	"mds" : "MDS",
	"dendro" : "Agl. Clust."
}
identical = [i for i in range(N)] 
 
answers = [["Метрика", "Алгоритм", "NDS", "CANR", "OANC", "TONC", "ANRA", "UP", "UMC"]]
answers_lkh = [["Метрика", "CANR", "TONC",  "ANRA", "UP", "UMC"]]
for metric in metrics.metrics_list:	
	dist =	model.get_topics_distances(metric=metric)	
	research.report_html("<h2>Метрика %s</h2>" % metric)
	research.show_matrix(dist)
	
	answers.append([
			metric, 
			"No arranging", 
			"%.04f" % arr.NDS(dist, identical),
			"%.04f" % arr.CANR(dist, identical),
			"%.06f" % arr.OANC(dist, identical),
			"%.04f" % arr.TONC(dist, identical),			
			"%.02f" % arr.ANRA(C, identical),
			"%.02f" % arr.UP(C, identical),
			"%.04f" % arr.UMC(C, dist),
		])
	
	for mode in modes:
		perm = arr.get_arrangement_permutation(dist, mode)
		answers.append([
			"", 
			mode_names[mode], 
			"%.04f" % arr.NDS(dist, perm),
			"%.04f" % arr.CANR(dist, perm),
			"%.06f" % arr.OANC(dist, perm),
			"%.04f" % arr.TONC(dist, perm),
			"%.02f" % arr.ANRA(C, identical),
			"%.02f" % arr.UP(C, perm),
			""
		])
		
		if mode == "hamilton":
			answers_lkh.append([metric,
				"%.04f" % arr.CANR(dist, perm),
				"%.04f" % arr.TONC(dist, perm),
				"%.04f" % arr.ANRA(C, perm),
				"%.02f" % arr.UP(C, perm),
				"%.04f" % arr.UMC(C, dist)
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
