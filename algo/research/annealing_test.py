# -*- coding: utf-8 -*-
import numpy as np 
import json 
from algo.arranging.hamilton_path import HamiltonPath

try:
	params = json.loads(research.problem.params)
except:
	pass
	
model = research.model
topics = model.get_topics()



research.report_html("<h1>Annealing test.</h1>")
dist =	model.get_topics_distances(metric="euclidean")	
N = dist.shape[0]	
annealing_grid = [1, 5, 10, 20, 50, 100]
topics_grid = range(4, 24)

algo_names = ["exact", "branch-2", "branch-3", "greedy"] + ["annealing-" + str(i) for i in annealing_grid]
answers = dict()
for algo_name in algo_names:
	answers[algo_name] = dict()


for topics_count in topics_grid:
	matrix = dist[0 : topics_count, 0 : topics_count] 
	research.report("%d topics" % topics_count)
	#research.show_matrix(matrix)
	hp = HamiltonPath(matrix)
	research.report("Качество вначале: " + str(hp.path_weight()))
	
	if topics_count <= 11:
		research.report_p()
		research.report("Точное решение.")
		hp = HamiltonPath(matrix)
		hp.solve_branch(cut=100) 
		research.report("Время " + str(hp.elapsed))
		research.report("Качество " + str(hp.path_weight()))
		answers["exact"][topics_count] = {"time": hp.elapsed, "q": hp.path_weight()}	
	
	if topics_count <= 16:		
		research.report_p()
		research.report("Метод ветвей и границ (3).")
		hp = HamiltonPath(matrix)
		hp.solve_branch(cut=3) 
		research.report("Время " + str(hp.elapsed)) 
		research.report("Качество " + str(hp.path_weight()))	 
		answers["branch-3"][topics_count] = {"time": hp.elapsed, "q": hp.path_weight()}	
	
	research.report_p()
	research.report("Метод ветвей и границ (2).")
	hp = HamiltonPath(matrix)
	hp.solve_branch(cut=2) 
	research.report("Время " + str(hp.elapsed)) 
	research.report("Качество " + str(hp.path_weight()))	
	answers["branch-2"][topics_count] = {"time": hp.elapsed, "q": hp.path_weight()}	
	exact_quality = hp.path_weight()
  
	research.report_p()
	research.report("Жадный алгоритм.")
	hp = HamiltonPath(matrix)
	hp.solve_nn()	
	research.report("Время " + str(hp.elapsed)) 
	research.report("Качество " + str(hp.path_weight()))
	answers["greedy"][topics_count] = {"time": hp.elapsed, "q": hp.path_weight()}	
	
	for time in annealing_grid:
		research.report_p()
		research.report("Симмуляция отжига (%d сек)." % time)
		hp = HamiltonPath(matrix)
		hp.solve_annealing(run_time=time)
		research.report("Время " + str(hp.elapsed))
		research.report("Качество " + str(hp.path_weight())) 

		answers["annealing-" + str(time)][ topics_count] = {"time": hp.elapsed, "q": hp.path_weight()}	
	  
		axes = research.gca()
		axes.plot(hp.chart_time, hp.chart_weight)
		axes.plot([0, hp.elapsed], [exact_quality, exact_quality]) 
		axes.set_xlabel("Time (s)")
		axes.set_ylabel("Quality")
		axes.set_title("Annealing dynamics (%d topics)" % topics_count, fontsize=15)
		research.report_picture() 
	
	research.report_html("<hr>")
	

time_charts = dict()
quality_charts = dict()

for algo_name in algo_names:
	time_charts[algo_name] = []
	quality_charts[algo_name] = []
	
import json
research.report(json.dumps(answers))
	

for topics_num in topics_grid:
	for algo_name in algo_names:
		try:
			time_charts[algo_name].append(answers[algo_name][topics_num]["time"])
			quality_charts[algo_name].append(answers["branch-2"][topics_num]["q"] / answers[algo_name][topics_num]["q"])
		except:
			pass
			
axes = research.gca(figsize=(20,10))
for algo_name in algo_names:
	values = time_charts[algo_name]
	axes.plot(topics_grid[0:len(values)], values, label=algo_name)
axes.set_xlabel("Number of topics", fontsize=20)
axes.set_ylabel("Time", fontsize=20)
axes.set_title("Running time of arranging algorithms", fontsize=30)
axes.set_xlim(topics_grid[0], topics_grid[0] + len(topics_grid) - 1)

lgd = axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))
research.report_picture(bbox_extra_artists=(lgd,), width=800)

axes = research.gca(figsize=(20,10))
for algo_name in algo_names:
	values = quality_charts[algo_name]
	axes.plot(topics_grid[0:len(values)], values, label=algo_name)
axes.set_xlabel("Number of topics", fontsize=20)
axes.set_ylabel("Quality", fontsize=20)
axes.set_title("Relative quality of arranging algorithms", fontsize=30)
axes.set_xlim(topics_grid[0], topics_grid[0] + len(topics_grid) - 1)
lgd = axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))
research.report_picture(bbox_extra_artists=(lgd,), width=800)

