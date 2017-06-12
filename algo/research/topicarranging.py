# -*- coding: utf-8 -*-
import numpy as np 
import json 
import algo.arranging.quality as qual
import algo.arranging.base as arranging_base
import algo.arranging.metrics as metrics


# Makes linear transformation, such as minimal non-diagonal element becomes 0 and maximal element becomes 1
def normalize_metric_matrix(x):
	N = x.shape[0]
	x_max = np.max(x)
	x_min = np.min(x + x_max * np.identity(N))
	return (x - x_min) * (1.0/(x_max-x_min))
	

def scatter_and_regression(ax, x, y):
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]
    ax.scatter(x, y)    
    ax.plot(x, m*x + c, 'r')  

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


	
modes = ["none", "hamilton", "hamilton_annealing", "tsne", "mds", "dendro"] 
mode_names = {
	"none" : "No arranging",
	"hamilton" : "LKH",
	"tsne" : "t-SNE",
	"mds" : "MDS",
	"dendro" : "Agl. Clust.",
	"hamilton_annealing" : "Annealing"
}

 
answers = [["Метрика", "Алгоритм", "NDS", "MNR", "ADP", "AMND", "ADNP", "AMC"]]
answers_lkh = [["Метрика", "MNR", "ADP", "AMND", "ADNP", "AMC"]]


dist_all = dict()
for metric in metrics.metrics_list:	
	dist_all[metric] = model.get_topics_distances(metric=metric)
	
	
# Assessment-distance curves
ADC = dict()
	
	
for metric in metrics.metrics_list:	
	dist = dist_all[metric]
	research.report_html("<h2>Метрика %s</h2>" % metric)
	research.show_matrix(dist)
	
	
	# Assessment-Distance correlation plot
	ax = research.gca(figsize=(10,10))	
	#scatter_and_regression(ax, qual.flatten_symmetric_matrix(dist), qual.flatten_symmetric_matrix(C))
	ax.scatter(qual.flatten_symmetric_matrix(dist), qual.flatten_symmetric_matrix(C))
	ax.set_xlabel("Metric (%s)" % metric, fontsize=20)
	ax.set_ylabel("Assessment", fontsize=20)
	ax.tick_params(labelsize=15) 
	research.report_picture(width=400, name=("AD_scatter_%s_%s" % (str(research.dataset), metric)))

	
	for mode in modes:
		perm = arranging_base.get_arrangement_permutation(dist, mode, model=research.model)
		answers.append([
			(metric if mode == "none" else ""), 
			mode_names[mode], 
			"%.04f" % qual.NDS(dist, perm),
			"%.04f" % qual.MNR(dist, perm), 
			"%.02f" % qual.ADP(C, perm),
			"%.02f" % qual.AMND(C, perm),
			"%.02f" % qual.ADNP(C, perm),
			("%.04f" % qual.AMC(C, dist) if mode=="none" else "")
		])
		
		if mode == "hamilton":
			answers_lkh.append([metric,
				"%.04f" % qual.MNR(dist, perm), 
				"%.02f" % qual.ADP(C, perm),
				"%.02f" % qual.AMND(C, perm),
				"%.04f" % qual.ADNP(C, perm),
				"%.02f" % qual.AMC(C, dist)
			])
			ADC[metric] = qual.DDC(C, perm)
		
			
		
		# DDC Chart
		if mode == "hamilton":
			#CDC = qual.CDC(dist, perm)
			
			ax = research.gca(figsize=(15,10))
			ax.set_xlabel("d", fontsize=30)
			ax.set_ylabel("DDC", fontsize=30)
			
			for target_metric in metrics.metrics_list:
				DDC = qual.DDC(normalize_metric_matrix(dist_all[target_metric]), perm)
				lw = (5 if (metric == target_metric) else 2)
				ax.plot(range(1,N-1), DDC, label=target_metric, linewidth = lw)
			lgd = ax.legend(loc='best', fontsize=20)
			lgd.get_frame().set_alpha(0.8)
			ax.tick_params(labelsize=20) 
			ax.set_ylim([0,1])
			research.report_picture(width=600, name=("DDC_%s_%s" % (str(research.dataset), metric)))
		
		

research.report("Assessment-Distance Curves")			
ax = research.gca(figsize=(15,10))
ax.set_xlabel("d", fontsize=30)
ax.set_ylabel("ADC", fontsize=30)
for metric in metrics.metrics_list:
	ax.plot(range(1,N-1), ADC[metric], label=metric, linewidth=2)
lgd = ax.legend(loc='best', fontsize=20)
lgd.get_frame().set_alpha(0.8)
ax.tick_params(labelsize=20) 
research.report_picture(width=600, name=("ADC_%s" % str(research.dataset)) )



research.report_table(answers)
research.report_table(answers_lkh)
