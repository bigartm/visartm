from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.template import RequestContext, Context, loader
from datasets.models import Dataset, Document, Term, Modality
from models.models import ArtmModel, Topic, TopTerm, TopicInDocument, TopicRelated, TopicInTerm, DocumentInTopic, TopicInTopic
from django.http import HttpResponse, HttpResponseNotFound
import os
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
	
	if model == None:
		context = Context({'dataset': dataset,
						'document': document, 
						'document_paragraphs': lines})
		return render(request, 'visual/document.html', context)
	
	
	highlight_terms = True 
	if "highlight_terms" in request.COOKIES and request.COOKIES["highlight_terms"] == "false":
		highlight_terms = False
	
	
	
	
	topics_count = [int(x) for x in model.topics_count.split()]
	target_layer = model.layers_count
	
	word_index_file_name = os.path.join(settings.DATA_DIR, "datasets", dataset.text_id, "word_index", str(document.model_id) + ".txt")
	model_folder = os.path.join(settings.DATA_DIR, "models", str(model.id))
	phi_file_name = os.path.join(model_folder, "phi.npy")
	theta_file_name = os.path.join(model_folder, "theta.npy")
	phi = np.load(phi_file_name)
	theta = np.load(theta_file_name)
	theta_t = theta.transpose()
	documents_count = theta.shape[1] 
	
	
		
	 
	 
	# Get topic distribution in document (actually, column form Theta)
	topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("id_model")
	shift = 0
	for i in range(1, target_layer):
		shift += topics_count[i]
	
	topics_list = []
	document_matrix_id = document.model_id - 1
	for topic_id in range(0, topics_count[target_layer]):
		topics_list.append((theta[shift + topic_id, document_matrix_id], topic_id))
	
	topics_list.sort(reverse = True) 

	topics_hl_count = 4
	# TODO: from CSS
	colors = ["grey","#ff0000", "#00ff00", "#0000ff", "#ffff00"]
	
	hl_topics = [0 for i in range(0, topics_count[target_layer])]
	
	
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
				"color" : color, 
				"title": topic.title, 
				"weight": weight, 
				#"weight_text": "{0:.1f}%".format(100 * weight)
				"url": "/visual/topic?id=" + str(topic.id),
			})
	
	topics.append({
			"color" : colors[0], 
			"title": "Other", 
			"weight": other_weight, 
			#"weight_text": "{0:.1f}%".format(100 * other_weight),
			"url": "/visual/doc_all_topics?id=" + str(document.id), 
		})
		 
		
	# word highlight
	if highlight_terms:
		phi_layer = phi[:, shift : shift + topics_count[target_layer]]
		lines_count = len(lines)
		terms_index = [[] for i in range(0,lines_count)]
		with open(word_index_file_name, 'r', encoding = 'utf-8') as f:
			for word_index_line in f.readlines():
				word_info = word_index_line.split()
				line = int(word_info[0]) - 1
				start_pos = int(word_info[1])
				length = int(word_info[2])
				word_id = int(word_info[3])			 
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
	documents_index = Document.objects.filter(dataset = dataset).order_by("model_id")
	dist = np.zeros(documents_count)
	self_distr = theta_t[document_matrix_id]
	for other_document_id in range(0, documents_count):
		dist[other_document_id] = euclidean(self_distr, theta_t[other_document_id])
	
	idx = np.argsort(dist)[1:21]
	
	related_documents = [documents_index[int(i)] for i in idx]
	
	
	template = loader.get_template('visual/document.html')
	context = Context({'dataset': dataset,
					   'document': document, 
					   'model': model, 
					   'topics': topics,
					   'document_paragraphs': lines,
					   'related_documents' : related_documents})
	return HttpResponse(template.render(context))  
	
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
	
def get_theme_css(request):
	theme_name = "light"
	if "color_theme" in request.COOKIES:
		theme_name = request.COOKIES["color_theme"]
	css_file = os.path.join(settings.BASE_DIR, "static", "themes", theme_name + ".css") 
	with open(css_file) as file: 
		return HttpResponse(file.read(), content_type='text/css')  

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
	
import random
def visual_temporal_dots(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]

	# Now extracting months (in future need prepare them when loading dataset)
	model = get_model(request, dataset)
	doc_topics = DocumentInTopic.objects.filter(model = model)
	topics = Topic.objects.filter(model = model).order_by("id_model")
	
	monthes_set = set()
	
	for doc_topic in doc_topics:
		time = doc_topic.document.time
		monthes_set.add ((time.year, time.month))
	
	monthes_set = list(monthes_set)
	monthes_set.sort()
	
	monthes_send = []
	monthes_reverse_index = dict()
	i = 0
	for month in monthes_set:
		monthes_send.append({"X": i, "name": str(month[1]) + "/" + str(month[0])})
		monthes_reverse_index[month] = i
		i += 1	
		
	print("Monthes ready.")
	documents_send = [{"X": monthes_reverse_index[(doc_topic.document.time.year, doc_topic.document.time.month)] + 0.01 * random.randint(0,99), 
					   "Y": doc_topic.topic.id_model  + 0.5,
					   "document": doc_topic.document} for doc_topic in doc_topics]
		
	topics_send = []
	i = 0
	for topic in topics:
		topics_send.append({"Y": i, "topic": topic})
		i+=1
	
	context = Context({'dataset': dataset,
						'monthes': monthes_send,
					    'documents': documents_send,
					    'topics': topics_send})
	return render(request, 'visual/temporal_dots.html', context)
	
def visual_temporal_squares(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	group_by = request.GET["group_by"]
	model = get_model(request, dataset)  
	
	context = Context({'dataset': dataset,
					   'data': model.get_temporal_cells(group_by = group_by)})
	
	return render(request, 'visual/temporal_squares.html', context)

	
def visual_circles(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	model = get_model(request, dataset)
	file_name = os.path.join(settings.DATA_DIR, "models", str(model.id), "circles.json")
	print(file_name)
	with open(file_name) as file: 
		root = file.read();  
		
	context = Context({'dataset': dataset,
					   'model': model,
					   'root': root})
					   
	return render(request, 'visual/circles.html', context)
	
	
def visual_tsne(request):
	return HttpResponse("t-SNE not implemented.")

def foamtree(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	model = get_model(request, dataset)
	file_name = os.path.join(settings.DATA_DIR, "models", str(model.id), "foamtree.json")
	print(file_name)
	with open(file_name) as file: 
		root = file.read();  
		
	context = Context({'dataset': dataset,
					   'model': model,
					   'root': root})
					   
	return render(request, 'visual/foamtree.html', context)	
	
def visual_voronoi(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]	
	context = Context({'dataset': dataset})
	return render(request, 'visual/voronoi.html', context)

	
def tree_presentation(topic, model):
	ret = "<li><a href='/visual/topic?id=" + str(topic.id) + "'>" + topic.title + "</a></li>"
	children = TopicInTopic.objects.filter(model = model, parent = topic)
	if len(children) > 0:
		ret += "<ul>" + "".join([tree_presentation(topic.child, model) for topic in children]) + "</ul>"
	return ret

def html_tree(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	model = get_model(request, dataset) 
	root_topic = Topic.objects.filter(model = model, layer = 0)[0] 
	
	topics = TopicInTopic.objects.filter(model = model, parent = root_topic)
	tree = "<ul>" + "".join([tree_presentation(topic.child, model) for topic in topics]) + "</ul>"
	
	context = Context({'dataset': dataset,
					   'tree': tree})
	return render(request, 'visual/html_tree.html', context)
 