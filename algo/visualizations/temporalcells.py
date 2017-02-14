from models.models import Topic, TopicInTopic

import re
import json


def top_words_html(tw):
	i = 0
	ret = ""
	for word in tw:
		i+= 1
		ret += word
		if i % 3 == 0:
			ret += "<br>"
		else:
			ret += " "
	return ret

def visual(model, params): 		
	group_by = params[1]		# year,month,week,day 
	topics = Topic.objects.filter(model = model, layer = model.layers_count).order_by("spectrum_index")
	
	cells, dates = model.group_matrix(group_by=group_by, named_groups=True)
	topics_count = len(topics)
	dates_count = len(dates)
	dates_send = [{"X": i, "name": dates[i]} for i in range(dates_count)]
		
	# Find maximal sizes for norming
	max_size = 0
	column_max_size = [0 for i in range(dates_count)]
	row_max_size = [0 for i in range(topics_count)]	
	for x in range(dates_count):
		for y in range(topics_count):
			size = len(cells[x][y])
			max_size = max(max_size, size)
			column_max_size[x] = max(column_max_size[x], size)
			row_max_size[y] = max(row_max_size[y], size)
			
		
	cells_send = []
	for x in range(dates_count):
		for y in range(topics_count):
			size = len(cells[x][y])
			# [all, row, column]
			intense = [size / max_size, size / row_max_size[y], size / column_max_size[x]]
			cells_send.append({"X" : x, "Y" : y, "intense": intense, "docs" : cells[x][y]})
	
	topics_send = [{"Y": topic.spectrum_index,
					"topwords": top_words_html(topic.top_words(count=15)),
					"name": ' '.join(re.findall(r"[\w']+", topic.title)[0:2])} for topic in topics]
	
	# in case of hierarchical model we want show tree
	high_topics_send = []
	lines_send = []
	if model.layers_count > 1:
		high_topics = Topic.objects.filter(model = model, layer = model.layers_count - 1)
		high_topics_temp = []
		for topic in high_topics:
			children = TopicInTopic.objects.filter(parent = topic)
			positions = [relation.child.spectrum_index for relation in children]
			avg = sum(positions)/float(len(positions))
			high_topics_temp.append({"mass_center_y":avg, "name": ' '.join(re.findall(r"[\w']+", topic.title)[0:2]), "positions": positions})
		high_topics_temp.sort(key = lambda x: x["mass_center_y"])
		
		i = 0
		K = len(topics_send) / float(len(high_topics_temp))
		for el in high_topics_temp:		
			pos_y = K*(i+0.5)
			high_topics_send.append({"Y": pos_y, "name" : el["name"]})
			for j in el["positions"]:
				lines_send.append({"from_y": pos_y, "to_y": j})
			i += 1
	#-------------------------------------------
	
	return  "cells=" + json.dumps(cells_send) + ";\n" + \
			"dates=" + json.dumps(dates_send) + ";\n" + \
			"topics=" + json.dumps(topics_send) + ";\n" + \
			"high_topics=" + json.dumps(high_topics_send) + ";\n" + \
			"lines=" + json.dumps(lines_send) + ";\n" 
