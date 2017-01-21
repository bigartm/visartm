from django.shortcuts import render, redirect
from django.template import RequestContext, Context
from datasets.models import Dataset, Document, Term, Modality
from models.models import ArtmModel, Topic, TopTerm, TopicInDocument, TopicRelated, TopicInTerm, DocumentInTopic, TopicInTopic
from django.http import HttpResponse, HttpResponseNotFound
import os
import json
from django.conf import settings
import numpy as np
import pandas as pd
from scipy.spatial.distance import euclidean, cosine
from django.conf import settings
from visual.models import GlobalVisualization
import struct
from threading import Thread
from datetime import datetime
import artmonline.views as general_views

	
	
def visual_document(request): 
	if 'id' in request.GET:
		document = Document.objects.filter(id = request.GET['id'])[0]
		dataset = document.dataset
	else:
		dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
		document = Document.objects.filter(dataset = dataset, index_id = int(request.GET['iid']))[0]
	
	context = {'dataset': dataset, 'document': document}
	
	model = get_model(request, dataset)	
	if not model is None:
		context['model'] = model

	if not model is None:
		topics_count = [int(x) for x in model.topics_count.split()]
		target_layer = model.layers_count
		#model_folder = os.path.join(settings.DATA_DIR, "models", str(model.id))
		phi = model.get_phi()
		theta = model.get_theta()
		theta_t = theta.transpose()
		documents_count = dataset.documents_count
			 

		topics_hl_count = 4 
		hl_topics = [0 for i in range(0, topics_count[target_layer])]
	
	# Topics distribution in document (actually, column form Theta)
	topics = []
	if not model is None:
		topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("id_model")
		shift = 0
		for i in range(1, target_layer):
			shift += topics_count[i]
		topics_list = []
		document_matrix_id = document.index_id - 1
		for topic_id in range(0, topics_count[target_layer]):
			topics_list.append((theta[shift + topic_id, document_matrix_id], topic_id))
		topics_list.sort(reverse = True) 
		
		topics = []
		idx = 0
		other_weight = 1
		for (weight, topic_id) in topics_list:
			if weight < 0.05:
				break
			idx +=1 
			if idx <= topics_hl_count:
				topic = topics_index[topic_id] 
				hl_topics[topic.id_model] = idx
				other_weight -= weight
				topics.append({
					"i" : idx, 
					"title": topic.title, 
					"weight": weight,  
					"url": "/visual/topic?id=" + str(topic.id),
				})
		
		topics.append({
				"i" : 0, 
				"title": "Other", 
				"weight": other_weight,  
				"url": "/visual/doc_all_topics?id=" + str(document.id), 
			})
	context['topics'] = topics
	


		
	if 'mode' in request.GET and request.GET['mode'] == 'bow':
		# reading bag of words
		bow = document.bag_of_words
		
		unique_terms_count = len(bow) // 6 
		
		bow_entries = []
		for i in range(unique_terms_count):
			bow_iid = struct.unpack('I', bow[6*i : 6*i+4])[0]
			bow_count = struct.unpack('H', bow[6*i+4 : 6*i+6])[0]
			bow_entries.append((-bow_count, bow_iid))
		
		bow_entries.sort()
		bow_send = ""
		
		cut_bow = 1
		if "cut_bow" in request.COOKIES:
			cut_bow = int(request.COOKIES["cut_bow"])
		
		prfx = "<a href = '/term?ds=" + str(dataset.id) + "&iid="
		rest = unique_terms_count
		for x in bow_entries:
			cnt = -x[0]
			iid = x[1]
			if cnt <= cut_bow:
				bow_send += str(rest) + " terms, which occured " + str(cut_bow) + " times or less, aren't shown." 
				break
			bow_send += prfx + str(iid) + "'>" + Term.objects.filter(dataset = dataset, index_id = iid)[0].text + "</a>: " + str(cnt) + "<br>"
			rest -= 1
		context['bow'] = bow_send
	else:			
		if not dataset.text_provided:
			context['lines'] = ["","Text wasn't provided"]
		else:
			file_name = os.path.join(settings.DATA_DIR, "datasets", dataset.text_id, "documents", str(document.index_id) + ".txt")
			with open(file_name, 'r', encoding = 'utf-8') as f:
				lines = f.readlines()
				
			highlight_terms = dataset.word_index_provided 
			if "highlight_terms" in request.COOKIES and request.COOKIES["highlight_terms"] == "false":
				highlight_terms = False
			 
			# Word highlight
			if highlight_terms:
				if not model is None:
					index_to_matrix = dataset.get_index_to_matrix()
					phi_layer = phi[:, shift : shift + topics_count[target_layer]]
					theta_t_layer = theta_t[document_matrix_id, shift : shift + topics_count[target_layer]]
				lines_count = len(lines)
				entries_index = [[] for i in range(0,lines_count)]
				word_index_file_name = os.path.join(settings.DATA_DIR, "datasets", dataset.text_id, "word_index", str(document.index_id) + ".txt")
				with open(word_index_file_name, 'r', encoding = 'utf-8') as f:
					for word_index_line in f.readlines():
						word_info = word_index_line.split()
						line = int(word_info[0]) - 1
						start_pos = int(word_info[1])
						length = int(word_info[2])
						term_index_id = int(word_info[3])			
						if model is None:
							entries_index[line].append((start_pos, length, term_index_id, 0)) 
						else:
							term_matrix_id = index_to_matrix[term_index_id]
							topic_id = np.argmax(phi_layer[term_matrix_id] * theta_t_layer)			
							entries_index[line].append((start_pos, length, term_index_id, hl_topics[topic_id])) 
				
				for i in range(0, lines_count):
					old_line = lines[i]
					new_line = ""
					cur_pos = 0
					old_line_length = len(old_line)
					for (start_pos, length, term_index_id, class_id) in entries_index[i]:
						if (cur_pos < start_pos):
							new_line += old_line[cur_pos : start_pos]
							cur_pos = start_pos
						new_line += "<a href = '/term?ds=" + str(dataset.id) + "&iid=" + str(term_index_id) + "' class = 'nolink tpc" + str(class_id) + "'>"
						new_line += old_line[cur_pos : cur_pos + length]
						new_line += "</a>"
						cur_pos += length
					
					if (cur_pos < old_line_length):
						new_line += old_line[cur_pos : old_line_length]
						cur_pos = old_line_length
					lines[i] = new_line
			context['lines'] = lines
				
		
	# Related documents 
	if not model is None:
		documents_index = Document.objects.filter(dataset = dataset).order_by("index_id")
		dist = np.zeros(documents_count)
		self_distr = theta_t[document_matrix_id]
		for other_document_id in range(0, documents_count):
			dist[other_document_id] = euclidean(self_distr, theta_t[other_document_id])
		
		idx = np.argsort(dist)[1:21]		
		context['related_documents'] = [documents_index[int(i)] for i in idx] 
					 
	return render(request, 'datasets/document.html', Context(context))
	
def visual_document_all_topics(request): 	
	document = Document.objects.filter(id = request.GET['id'])[0]
	model = get_model(request, document.dataset)
	topics_count = [int(x) for x in model.topics_count.split()] 
	target_layer = model.layers_count
	document_matrix_id = document.model_id - 1
	 
	theta_file_name = os.path.join(settings.DATA_DIR, "models", str(model.id), "theta.npy")
	theta = np.load(theta_file_name) 
	
	  
	topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("id_model")
	shift = 0
	for i in range(1, target_layer):
		shift += topics_count[i]
	
	topics_list = []
	for topic_id in range(0, topics_count[target_layer]):
		topics_list.append((theta[shift + topic_id, document_matrix_id], topics_index[topic_id]))
	
	topics_list.sort(reverse = True)
	 
		  
	context = Context({'document': document,  
					   'topics': [{"weight": 100*i[0], "topic": i[1]} for i in topics_list]})
					   
	return render(request, 'visual/document_all_topics.html', context) 


# from cookies
def get_model(request, dataset):
	key = "model_" + str(dataset.id)
	
	try:
		return ArtmModel.objects.filter(id = int(request.COOKIES[key]))[0]
	except:
		pass
		
	try:
		ret = ArtmModel.objects.filter(dataset = dataset)[0]
		request.COOKIES[key] = ret.id
		return ret
	except:
		pass
				
	return None

	
def visual_global(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	model = get_model(request, dataset)
	visual_name = request.GET['type']
	
	if model == None:
		return general_views.message(request, "You have to create model first.<br>" + \
							"<a href='/models/create?dataset=" + dataset.text_id + "'>Create model</a><br>"     + \
							"<a href='/dataset?dataset=" + dataset.text_id + "'>Return to dataset</a><br>")

							
	if 'try' in request.GET and request.GET['try'] == 'again':
		GlobalVisualization.objects.filter(model = model, name = visual_name).delete()
		return redirect("/visual/global?type=" + visual_name + "&dataset=" + dataset.text_id)
		
		
	try:
		visualization = GlobalVisualization.objects.filter(model = model, name = visual_name)[0]			
	except:
		visualization = GlobalVisualization()
		visualization.name = visual_name
		visualization.model = model
		visualization.status = 0
		visualization.save()
		   
		t = Thread(target = GlobalVisualization.render, args = (visualization,), daemon = True)
		t.start()
	
	if visualization.status == 0:
		return general_views.wait(request, "Pending...", visualization.start_time, period = "2") 
	elif visualization.status == 2:
		return general_views.message(request, "Error during rendering.<br>" + visualization.error_message.replace('\n', "<br>") +   \
				"<br><br><a href='/visual/global?type=" + visual_name + \
				"&dataset=" + dataset.text_id + "&try=again'>Try again</a>")
	
	
	data_file_name = os.path.join(model.get_visual_folder(), visual_name + ".txt")
	with open(data_file_name, "r", encoding = 'utf-8') as f:
		data = f.read()
	context = Context({'dataset': dataset,
						'data': data,
						'no_footer': True})				   
	return render(request, "visual/" + visual_name.split('_')[0] + ".html", context)
 