# -*- coding: utf-8 -*-
import numpy as np 
import json 
import algo.arranging.base as arr
import algo.metrics as metrics

model = research.model
topics = model.get_topics()


try:
	if research.problem.model != research.model:
		raise ValueError("Model differs from the assessed one!")

	ass = np.array(research.problem.get_results())
	N = ass.shape[0]
except:
	N = len(topics)
	ass = np.zeros((N, N))


research.report("Темы:")
research.report_table([[str(topic.index_id), topic.title] for topic in topics])
	

modes = ["hamilton", "tsne", "mds", "dendro"] 
identical = [i for i in range(N)] 
 
answers = [["metric", "mode", "PW", "ANR", "OAC", "TOC"]]
for metric in metrics.metrics_list:	
	dist =	model.get_topics_distances(metric=metric)	
	research.report_html("<h2>Метрика %s</h2>" % metric)
	research.show_matrix(dist)
	
	answers.append([
			metric, 
			"No arranging", 
			"%.03f" % arr.neigbor_distances_sum(dist, identical),
			"%.02f" % arr.average_neigbour_rank(dist, identical),
			"%.02f" % arr.obtuse_angle_conserving(dist, identical),
			"%.02f" % arr.triple_order_conserving(dist, identical),
			#"%.02f" % arr.user_score(ass, identical)
		])
	
	for mode in modes:
		perm = arr.get_arrangement_permutation(dist, mode)
		answers.append([
			metric, 
			mode, 
			"%.03f" % arr.neigbor_distances_sum(dist, perm),
			"%.02f" % arr.average_neigbour_rank(dist, perm),
			"%.02f" % arr.obtuse_angle_conserving(dist, perm),
			"%.02f" % arr.triple_order_conserving(dist, perm),
			#"%.02f" % arr.user_score(ass, perm)
		])

	
research.report_table(answers)
