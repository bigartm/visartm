# -*- coding: utf-8 -*-
import numpy as np 
import json 
from algo.hamilton.hamilton_path import HamiltonPath

try:
	params = json.loads(research.problem.params)
except:
	pass
	
model = research.model
topics = model.get_topics()



research.report("Темы:")
research.report_table([[str(topic.index_id), topic.title] for topic in topics])
	

 
for metric in ["euclidean", "hellinger", "cosine"]:	
	dist =	model.get_topics_distances(metric=metric)	
	research.report_html("<hr>")
	research.report_html("<h2>Метрика %s</h2>" % metric)
	research.report("Матрица расстояний")
	#research.report_table(dist)
	research.gca().imshow(dist, interpolation = "nearest")
	research.report_picture()

	
	hp = HamiltonPath(dist)
	research.report("Качество вначале: " + str(hp.path_weight()))
	
	
	research.report("Жадный алгоритм.")
	hp.solve_nn()
	research.report("Новая матрица расстояний.")
	research.gca().imshow(hp.permute_adj_matrix(), interpolation = "nearest")
	research.report_picture()
	research.report("Время " + str(hp.elapsed))
	research.report("Качество " + str(hp.path_weight()))

	'''
	research.report("Метод ветвей и границ.")
	hp.solve_branch(cut=2)
	research.report("Новая матрица расстояний.")
	research.gca().imshow(hp.permute_adj_matrix(), interpolation = "nearest")
	research.report_picture()
	research.report("Время " + str(hp.elapsed))
	research.report("Качество " + str(hp.path_weight()))	
	'''
	
	research.report("Симмуляция отжига.")
	hp = HamiltonPath(dist)
	hp.solve_annealing(run_time=10)
	research.report("Новая матрица расстояний.")
	research.gca().imshow(hp.permute_adj_matrix(), interpolation = "nearest")
	research.report_picture()


	research.report("Новый список тем.")
	research.report_table([[str(i), topics[i].title] for i in hp.path])

	research.report("Изменение качества во времени:")
	axes = research.gca()
	axes.plot(hp.chart_time, hp.chart_weight)
	axes.set_xlabel("Time (s)")
	axes.set_ylabel("Quality")
	research.report_picture()



	

