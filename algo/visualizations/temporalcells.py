#if __name__ != "__main__":
from datasets.models import Document
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
	intense_mode = params[2]	# row,column,all
	documents = Document.objects.filter(dataset = model.dataset)
	topics = Topic.objects.filter(model = model, layer = model.layers_count).order_by("spectrum_index")
	
	dn = DatesNamer()
	
	dates_hashes = set()
	for document in documents:
		dates_hashes.add(dn.date_hash(document.time, group_by))
	dates_hashes = list(dates_hashes)
	dates_hashes.sort()
	dates_send = []
	dates_reverse_index = dict()
	
	i = 0 
	for date_h in dates_hashes:
		dates_reverse_index[date_h] = i 
		dates_send.append({"X": i, "name": dn.date_name(date_h, group_by)})
		i += 1
		
	cells = dict()
	
	
	
	
	for topic in topics:
		for document in topic.get_documents():
			cell_xy = (dates_reverse_index[dn.date_hash(document.time, group_by)], topic.spectrum_index)
			if not cell_xy in cells:
				cells[cell_xy] = []
			cells[cell_xy].append(document.id)
		
	max_size = 0
	column_max_size = [0 for i in range(len(dates_send))]
	row_max_size = [0 for i in range(len(topics))]
	
	for key, value in cells.items():
		x = key[0]
		y = key[1]
		size = len(value)
		max_size = max(max_size, size)
		column_max_size[x] = max(column_max_size[x], size)
		row_max_size[y] = max(row_max_size[y], size)
		
		
	cells_send = []
	for key, value in cells.items():
		x = key[0]
		y = key[1]
		size = len(value)
		if intense_mode == "all":
			intense = size / max_size 
		elif intense_mode == "row":
			intense = size / row_max_size[y] 
		elif intense_mode == "column":
			intense = size / column_max_size[x] 
		
		cells_send.append({"X" : x, "Y" : y, "intense": intense, "docs" : value})
	
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
	
	
	return  "cells=" + json.dumps(cells_send) + ";\n" + \
			"dates=" + json.dumps(dates_send) + ";\n" + \
			"topics=" + json.dumps(topics_send) + ";\n" + \
			"high_topics=" + json.dumps(high_topics_send) + ";\n" + \
			"lines=" + json.dumps(lines_send) + ";\n" 

import datetime
class DatesNamer:
	def __init__(self):
		self.monthes = ["*", "Jan", "Feb", "Mar","Apr", "May", "Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

				
	def date_hash(self, date, group_by):
		if (group_by == "year"):
			return date.year
		elif (group_by == "month"):
			return date.month + 100 * date.year
		elif (group_by == "week"):
			return (date - datetime.datetime(1970, 1, 5, 0, 0, 0, 1)).days // 7
		elif (group_by == "day"):
			return date.day + 100 * date.month + 10000 * date.year
			
	def date_name(self, date_hash, group_by):
		global monthes
		if (group_by == "year"):
			return str(date_hash)
		if (group_by == "month"):
			return self.monthes[int(date_hash % 100)] + " " + str(int(date_hash / 100))  
		if (group_by == "week"): 
			monday = datetime.date(1970, 1, 5) + datetime.timedelta(days = 7 * date_hash)
			sunday = monday + datetime.timedelta(days=6)
			if monday.month == sunday.month:
				return "%s-%s %s %d" % (monday.day, sunday.day, self.monthes[monday.month], monday.year)
			elif monday.year == sunday.year:
				return "%s %s - %s %s %d" % (monday.day, self.monthes[monday.month], sunday.day, self.monthes[sunday.month], monday.year)
			else:
				return "%s %s %d - %s %s %d" % (monday.day, self.monthes[monday.month], monday.year, monday.day, self.monthes[sunday.month], sunday.year)
		elif (group_by == "day"):
			return str(date_hash % 100) + " " + self.monthes[ int(date_hash / 100) % 100] + " " + str(int(date_hash / 10000) % 100)

'''		 
if __name__ == "__main__":
    dn = DatesNamer()
    print(dn.date_name(20101110, "day") )
'''