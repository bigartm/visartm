# -*- coding: utf-8 -*-
import numpy as np 
import json 
import algo.arranging.base as arr

model = research.model
topics = model.get_topics()

if research.problem.model != research.model:
	raise VlueError("Model differs from the assessed one!")

ass = np.array(research.problem.get_results())
N = ass.shape[0]
research.show_matrix(ass)



research.report("Темы:")
research.report_table([[str(topic.index_id), topic.title] for topic in topics])
	
metrics = ["euclidean", "minkovsky", "hellinger", "cosine", "jaccard", "jsd"]
modes = ["hamilton_fast", "tsne", "mds", "dendro"] 
identical = [i for i in range(N)] 
 
answers = [["metric", "mode", "PW", "OAC", "US"]]
for metric in metrics:	
	dist =	model.get_topics_distances(metric=metric)	
	research.report_html("<h2>Метрика %s</h2>" % metric)
	research.show_matrix(dist)
	
	answers.append([
			metric, 
			"No arranging", 
			arr.path_weight(dist, identical),
			arr.obtuse_angle_conserving(dist, identical),
			arr.user_score(ass, identical)
		])
	
	for mode in modes:
		perm = arr.get_arrangement_permutation(dist, mode)
		answers.append([
			metric, 
			mode, 
			arr.path_weight(dist, perm),
			arr.obtuse_angle_conserving(dist, perm),
			arr.user_score(ass, perm)
		])

	
research.report_table(answers)
