from models.models import Topic, DocumentInTopic, TopicInTopic
import re
import json

def visual(model, params): 		
	group_by = params[1]
	doc_topics = DocumentInTopic.objects.filter(model = model)
	topics = Topic.objects.filter(model = model, layer = model.layers_count).order_by("spectrum_index")
	
	dates_hashes = set()
	for doc_topic in doc_topics:
		dates_hashes.add(date_hash(doc_topic.document.time, group_by))
	dates_hashes = list(dates_hashes)
	dates_hashes.sort()
	dates_send = []
	dates_reverse_index = dict()
	
	i = 0 
	for date_h in dates_hashes:
		dates_reverse_index[date_h] = i 
		dates_send.append({"X": i, "name": date_name(date_h, group_by)})
		i += 1
		
	cells = dict()
	
	
	
	for doc_topic in doc_topics:
		cell_xy = (dates_reverse_index[date_hash(doc_topic.document.time, group_by)], doc_topic.topic.spectrum_index)
		if not cell_xy in cells:
			cells[cell_xy] = []
		cells[cell_xy].append(doc_topic.document.id)
	
	max_intense = 0
	cells_send = []
	for key, value in cells.items():
		intense = len(value);
		max_intense = max(max_intense, intense)
		cells_send.append({"X" : key[0], "Y" : key[1], "intense": intense, "docs" : value})
	
	topics_send = [{"Y": topic.spectrum_index, "name": ' '.join(re.findall(r"[\w']+", topic.title)[0:2])} for topic in topics]
	
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
	
	
	return  "cells=" + json.dumps(cells_send) + ";\n" + \
			"dates=" + json.dumps(dates_send) + ";\n" + \
			"topics=" + json.dumps(topics_send) + ";\n" + \
			"high_topics=" + json.dumps(high_topics_send) + ";\n" + \
			"lines=" + json.dumps(lines_send) + ";\n" + \
			"max_intense=" + str(max_intense) + ";\n"


def date_hash(date, group_by):
	if (group_by == "year"):
		return date.year
	if (group_by == "month"):
		return date.month + 100 * date.year
	elif (group_by == "day"):
		return date.day + 100 * date.month + 10000 * date.year
		
def date_name(date_hash, group_by):
	if (group_by == "year"):
		return str(date_hash)
	if (group_by == "month"):
		return str(date_hash % 100) + "/" + str(int(date_hash / 100)) 
	elif (group_by == "day"):
		return str(date_hash % 100) + "/" + str( int(date_hash / 100) % 100) + "/" + str(int(date_hash / 1000000))  
