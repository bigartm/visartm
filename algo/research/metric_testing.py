# -*- coding: utf-8 -*-
import numpy as np 
import json 
import algo.metrics as metrics

model = research.model
layer = research.problem.layer
topics = model.get_topics(layer=layer)
N = len(topics)

if research.problem.model != research.model:
	raise VlueError("Model differs from the assessed one!")

research.report("Темы:")
research.report_table([[str(topic.index_id), topic.title] for topic in topics])

ass  = research.problem.get_results()
#research.show_matrix(ass)
research.report_table(ass)
	

research.report("В этом исследовании сравниваются различные метрики на столбцах матрицы Фи.")
research.report("Их результаты сравниваются с ассессорскими оценками близости тем.")
research.report("Меры качества:")
research.report("1. Q1-1 - число таких тем, для которых ближайшая тема по метрике совпала с ближайшей по оценкам.")
research.report("1. Q1-all - число таких тем, для которых ближайшая тема по метрике хотя бы одним ассессором считалась близкой")





 
	
 
answers = [["metric", "Q1-1", "Q1-all"]]

for metric in metrics.metrics_list:	
	research.report("Метрика %s..." % metric)
	dist = model.get_topics_distances(metric=metric, layer=layer)	
	#research.show_matrix(dist)
	research.report_table(dist)
	
	q_11 = 0
	q_all = 0
	for i in range(N):
		idx = np.argsort(dist[i])
		research.report (str(idx[1]))
		if (ass[i][idx[1]] == np.max(ass[i])):
			q_11+=1
		if (ass[i][idx[1]]>0):
			q_all+=1
		
	
	answers.append([
			metric, 
			q_11 / N,
			q_all / N			
		])
	 
	
research.report_table(answers)
