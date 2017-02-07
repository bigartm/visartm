# -*- coding: utf-8 -*-
import numpy as np 
import json 

params = json.loads(research.problem.params)
model = research.model
topics = model.get_topics()



research.report_text("Topics:")
research.report_table([[str(topic.index_id), topic.title] for topic in topics])
	

	
assessed_weights = np.zeros((len(topics), len(topics)))
for link in params["links"]:
	assessed_weights[link["id1"]][link["id2"]] = link["weight"]
	assessed_weights[link["id2"]][link["id1"]] = link["weight"]
	
research.report_text("Assessment:")
research.report_table(assessed_weights, format="%d")
research.gca().imshow(assessed_weights, interpolation = "nearest")
research.report_picture()

	
for metric in ["euclidean", "cosine", "hellinger"]:
	research.report_text("Distance (%s) between topics:" % metric)
	dist = model.get_topics_distances(metric=metric)
	research.report_table(dist, format="%.2f")
	research.gca().imshow(dist, interpolation = "nearest")
	research.report_picture()

	

