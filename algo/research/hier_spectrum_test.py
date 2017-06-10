# -*- coding: utf-8 -*-
import numpy as np 
import json 
import algo.arranging.base as arr
import algo.metrics as metrics

model = research.model

if model.layers_count !=2:
	raise ValueError("Ths research is only for 2-level hierarchical models!")

for metric in metrics.metrics_list:
	research.report("Metric %s" % metric)
	beta_range = np.linspace(-0.2,1.2,57)
	SCC_chart = []
	NDS1_chart = []
	NDS2_chart = []
	for beta in beta_range:
		model.arrange_topics(mode="hierarchical", metric = metric, beta=beta)
		SCC_chart.append(model.spectrum_crosses_count())
		NDS1_chart.append(model.neighbor_distance_sum(metric=metric, layer=1))
		NDS2_chart.append(model.neighbor_distance_sum(metric=metric, layer=2))
		#research.report("%f %d %f" % (beta, SCC_chart[-1], NDS2_chart[-1]))
		
	fig = research.get_figure(figsize=(20,20))

 
	ax3 = fig.add_subplot(313)
	ax3.set_xlabel(r"$\beta$", fontsize=25)
	ax3.set_ylabel(r"$NDS_2$", fontsize=25)
	ax3.plot(beta_range, NDS2_chart)
	
	ax2 = fig.add_subplot(312 )
	ax2.set_xlabel(r"$\beta$", fontsize=25)
	ax2.set_ylabel(r"$NDS_1$", fontsize=25)
	ax2.plot(beta_range, NDS1_chart )

	ax1 = fig.add_subplot(311 )
	ax1.set_xlabel(r"$\beta$", fontsize=25)
	ax1.set_ylabel("SCC", fontsize=25)
	ax1.plot(beta_range, SCC_chart )
	
	#fig.suptitle(r"Hierarchical spectrum quality, depending on $\beta$", fontsize=20)
	#axes.set_title(r"Hierarchical spectrum quality, depending on $\beta$")
	#lgd = axes.legend(loc='center left', bbox_to_anchor=(1, 0.5))
	research.report_picture(width=800)

