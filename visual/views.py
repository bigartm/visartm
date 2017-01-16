from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.template import RequestContext, Context, loader
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


	
	
def visual_document(request): 
	if 'id' in request.GET:
		document = Document.objects.filter(id = request.GET['id'])[0]
		dataset = document.dataset
	else:
		dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
		document = Document.objects.filter(dataset = dataset, model_id = request.GET['document'])[0]

	file_name = os.path.join(settings.DATA_DIR, "datasets", dataset.text_id, "documents", str(document.model_id) + ".txt")
	with open(file_name, 'r', encoding = 'utf-8') as f:
		lines = f.readlines()
	
	model = get_model(request, dataset)	
	
	highlight_terms = True 
	if "highlight_terms" in request.COOKIES and request.COOKIES["highlight_terms"] == "false":
		highlight_terms = False
	
	if not model is None:
		topics_count = [int(x) for x in model.topics_count.split()]
		target_layer = model.layers_count
		model_folder = os.path.join(settings.DATA_DIR, "models", str(model.id))
		phi_file_name = os.path.join(model_folder, "phi.npy")
		theta_file_name = os.path.join(model_folder, "theta.npy")
		phi = np.load(phi_file_name)
		theta = np.load(theta_file_name)
		theta_t = theta.transpose()
		documents_count = dataset.docs_count
			 

		topics_hl_count = 4
		# TODO: from CSS
		colors = ["grey","#ff0000", "#00ff00", "#0000ff", "#ffff00"]
		hl_topics = [0 for i in range(0, topics_count[target_layer])]
	
	# Topics distribution in document (actually, column form Theta)
	if not model is None:
		topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("id_model")
		shift = 0
		for i in range(1, target_layer):
			shift += topics_count[i]
		topics_list = []
		document_matrix_id = document.model_id - 1
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
			color = colors[0]
			if idx <= topics_hl_count:
				topic = topics_index[topic_id]
				color = colors[idx]
				hl_topics[topic.id_model] = idx
				other_weight -= weight
				topics.append({
					"i" : idx,
					"color" : color, 
					"title": topic.title, 
					"weight": weight, 
					#"weight_text": "{0:.1f}%".format(100 * weight)
					"url": "/visual/topic?id=" + str(topic.id),
				})
		
		topics.append({
				"i" : 0,
				"color" : colors[0], 
				"title": "Other", 
				"weight": other_weight, 
				#"weight_text": "{0:.1f}%".format(100 * other_weight),
				"url": "/visual/doc_all_topics?id=" + str(document.id), 
			})
	else:
		topics = []
		
	# Word highlight
	if highlight_terms:
		if not model is None:
			phi_layer = phi[:, shift : shift + topics_count[target_layer]]
		lines_count = len(lines)
		terms_index = [[] for i in range(0,lines_count)]
		word_index_file_name = os.path.join(settings.DATA_DIR, "datasets", dataset.text_id, "word_index", str(document.model_id) + ".txt")
		with open(word_index_file_name, 'r', encoding = 'utf-8') as f:
			for word_index_line in f.readlines():
				word_info = word_index_line.split()
				line = int(word_info[0]) - 1
				start_pos = int(word_info[1])
				length = int(word_info[2])
				word_id = int(word_info[3])			
				if model is None:
					terms_index[line].append((start_pos, length, word_id, 0)) 
				else:
					topic_id = np.argmax(phi_layer[word_id - 1])			
					terms_index[line].append((start_pos, length, word_id, hl_topics[topic_id])) 
		
		for i in range(0, lines_count):
			old_line = lines[i]
			new_line = ""
			cur_pos = 0
			old_line_length = len(old_line)
			for (start_pos, length, term_id, class_id) in terms_index[i]:
				if (cur_pos < start_pos):
					new_line += old_line[cur_pos : start_pos]
					cur_pos = start_pos
				new_line += "<a href = '/visual/term?dataset=" + dataset.text_id + "&term=" + str(term_id) + "' class = 'nolink tpc" + str(class_id) + "'>"
				new_line += old_line[cur_pos : cur_pos + length]
				new_line += "</a>"
				cur_pos += length
			
			if (cur_pos < old_line_length):
				new_line += old_line[cur_pos : old_line_length]
				cur_pos = old_line_length
			lines[i] = new_line
				
		
	# Related documents
	if not model is None:
		documents_index = Document.objects.filter(dataset = dataset).order_by("model_id")
		dist = np.zeros(documents_count)
		self_distr = theta_t[document_matrix_id]
		for other_document_id in range(0, documents_count):
			dist[other_document_id] = euclidean(self_distr, theta_t[other_document_id])
		
		idx = np.argsort(dist)[1:21]		
		related_documents = [documents_index[int(i)] for i in idx]
	else:
		related_documents = []

	context = Context({'dataset': dataset,
					   'document': document, 
					   'model': model, 
					   'topics': topics,
					   'document_paragraphs': lines,
					   'related_documents' : related_documents})
	return render(request, 'visual/document.html', context)
	
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
	
def visual_term(request):
	try:
		target_dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	except:
		return redirect("/")
		
	term = Term.objects.filter(dataset = target_dataset, model_id = request.GET['term'])[0]
	template = loader.get_template('visual/term.html')
	context = Context({'dataset': target_dataset,
					   'term': term, })
	return HttpResponse(template.render(context)) 

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
	  
	
def visual_temporal_squares(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	if not dataset.time_provided:
		return HttpResponse("Dataset " + dataset.name + " has no time marks, so you cannot build temporal visualization.")
	group_by = request.GET["group_by"]
	model = get_model(request, dataset)  
	 
	context = {'dataset': dataset,
				'data': model.get_temporal_cells(group_by = group_by),
				"temporal_spectrum": True,
				'no_footer': True}
				
	if "temporal_spectrum" in request.COOKIES and request.COOKIES["temporal_spectrum"] == "false":
		context["temporal_spectrum"] = False 
		
	return render(request, 'visual/temporal_squares.html', Context(context))

	 
	
def visual_global(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	model = get_model(request, dataset)
	type = request.GET['type']
	
	context = Context({'dataset': dataset,
					   'model': model,
					   'data': model.get_visual(type),
					   'no_footer': True})
					   
	return render(request, "visual/" + type + ".html", context)

	
	
def visual_voronoi(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]	
	context = Context({'dataset': dataset})
	return render(request, 'visual/voronoi.html', context)

	
def tree_presentation(topic, model):
	ret = "<li><a href='/visual/topic?id=" + str(topic.id) + "'>" + topic.title + "</a></li>"
	children = TopicInTopic.objects.filter(model = model, parent = topic).order_by("child__spectrum_index")
	if len(children) > 0:
		ret += "<ul>" + "".join([tree_presentation(topic.child, model) for topic in children]) + "</ul>"
	return ret

def html_tree(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	model = get_model(request, dataset) 
	root_topic = Topic.objects.filter(model = model, layer = 0)[0] 
	
	topics = TopicInTopic.objects.filter(model = model, parent = root_topic).order_by("child__spectrum_index")
	tree = "<ul>" + "".join([tree_presentation(topic.child, model) for topic in topics]) + "</ul>"
	
	context = Context({'dataset': dataset,
					   'tree': tree})
	return render(request, 'visual/html_tree.html', context)
 