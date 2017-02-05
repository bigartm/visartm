from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from datasets.models import Dataset, Document, Term, TermInDocument, Modality
from models.models import ArtmModel, Topic
from django.conf import settings
import visartm.views as general_views
from threading import Thread
from datetime import datetime
import os
 
def datasets_list(request):  
	datasets = Dataset.objects.filter(is_public = True)
	if request.user.is_authenticated == True:
		datasets |= Dataset.objects.filter(owner = request.user) 
		
	context = Context({'datasets': datasets})
	return render(request, 'datasets/datasets_list.html', context)
	
	
def	dataset_reload(request):	
	dataset = Dataset.objects.get(text_id = request.GET['dataset'])
	if request.user != dataset.owner:
		return HttpResponseForbidden("You are not owner.")
	dataset.status = 1
	dataset.creation_time = datetime.now()
	dataset.save()	
	
	
	if settings.THREADING:
		t = Thread(target = Dataset.reload_untrusted, args = (dataset, ), daemon = True)
		t.start()
	else:
		dataset.reload()
		
	return redirect("/dataset?dataset=" + dataset.text_id) 
	

def dataset_delete(request):
	dataset = Dataset.objects.get(id = request.GET['id'])
	if request.user != dataset.owner:
		return HttpResponseForbidden("You are not owner.")
	
	if 'sure' in request.GET and request.GET['sure'] == 'yes': 
		dataset.delete()
		return general_views.message(request, "Dataset was completely deleted.<br><a href ='/'>Return to start page</a>.")
	else:
		return general_views.message(request, 
				"Are you sure that you want delete dataset " + str(dataset) + " permanently?<br>" + 
				"<a href = '/datasets/delete?id=" + str(dataset.id) + "&sure=yes'>Yes</a><br>" +
				"<a href = '/dataset?dataset=" + dataset.text_id + "'>No</a>")		
	
def	dataset_create(request):	
	if request.method == 'GET': 
		existing_datasets = [dataset.text_id for dataset in Dataset.objects.all()]
		folders = os.listdir(os.path.join(settings.DATA_DIR, "datasets"))
		unreg = [i for i in folders if not i in existing_datasets]
		 
		context = Context({"unreg": unreg})
		return render(request, "datasets/create_dataset.html", context) 
	
	#print(request.POST)
	dataset = Dataset()
	if request.POST['mode'] == 'upload':
		dataset.upload_from_archive(request.FILES['archive'])
		#return HttpResponse("OK")
	else:
		dataset.text_id = request.POST['unreg_name']
	
	dataset.name = dataset.text_id 
	
	preprocessing_params = dict()
	if 'parse' in request.POST:
		preprocessing_params['parse'] = {
			'store_order' : ('store_order' in request.POST),
			'hashtags' : ('hashtags' in request.POST),
			'bigrams' : ('bigrams' in request.POST),
		}
		
	if 'filter' in request.POST:
		preprocessing_params['filter'] = {
			'lower_bound' : request.POST['lower_bound'],
			'upper_bound' : request.POST['upper_bound'],
			'upper_bound_relative' : request.POST['upper_bound_relative'],
			'minimal_length' : request.POST['minimal_length']
		}
		
	if 'custom_vocab' in request.POST:
		preprocessing_params['custom_vocab'] = True
		
	
	import json
	dataset.preprocessing_params = json.dumps(preprocessing_params)	
	#return HttpResponse(dataset.preprocessing_params)
	
	
	dataset.owner = request.user  
	dataset.status = 1
	dataset.creation_time = datetime.now()	
	dataset.save()	
	
	if settings.THREADING:
		t = Thread(target = Dataset.reload, args = (dataset, ), daemon = True)
		t.start()
	else:
		dataset.reload()
	
	return redirect("/dataset?dataset=" + dataset.text_id) 
	
	
from django.conf import settings
def visual_dataset(request):  
	if request.method == "POST":
		print(request.POST)
		dataset = Dataset.objects.get(text_id = request.POST['dataset'])
		dataset.name = request.POST['name']
		dataset.description = request.POST['description']
		dataset.preprocessing_params = request.POST['preprocessing_params']	
		dataset.is_public = ("is_public" in request.POST)
		dataset.save() 
		return redirect("/dataset?dataset=" + request.POST['dataset'] + "&mode=settings")
	
	
	dataset = Dataset.objects.get(text_id = request.GET['dataset'])
	if dataset.status == 1:
		return general_views.wait(request, dataset.read_log() + \
			"<br><a href = '/datasets/reload?dataset=" + dataset.text_id + "'>Reload</a>", dataset.creation_time)
	elif dataset.status == 2:
		return general_views.message(request, dataset.error_message.replace("\n","<br>") + \
			"<br><a href = '/datasets/reload?dataset=" + dataset.text_id + "'>Reload</a>")
	
	context = {'dataset': dataset}
	
	if "search" in request.GET:
		search_query = request.GET["search"]
		context['search_query'] = search_query
	
	mode = 'docs'
	if 'mode' in request.GET:
		mode = request.GET['mode'] 
		
	if mode == 'terms':
		print("Start term query")
		terms = Term.objects.filter(dataset = dataset)
		print("End term query")
		if "search" in request.GET and len(search_query) >= 2: 
			terms = terms.filter(text__icontains = search_query).order_by("text")
			context['search'] = True
		else:	
			terms = terms.order_by("-token_tf")[:250] 
		context['terms'] = terms
	elif mode == 'stats':
		from math import log
		terms = Term.objects.filter(dataset = dataset).order_by("-token_tf")
		word = ['word']
		freq = ['freq'] 
		x = 0
		last_y = -1
		print("loop in")
		for term in terms:
			y = term.token_tf
			if y != last_y:
				word.append(x)
				freq.append(y)
				last_y = y 
			x+=1	
		print("loop out")
		word.append(x)
		freq.append(y)		
		context['stats'] = {'word_freq':[word, freq]}
		
		if dataset.time_provided:
			import itertools
			date_list = ['date']
			count_list = ['count']
			documents = Document.objects.filter(dataset = dataset).order_by("time")
			for dt, grp in itertools.groupby(documents, key=lambda x: x.time.date()):
				date_list.append(str(dt))
				count_list.append(len(list(grp)))
			context['stats']['timeline'] = [date_list, count_list]
		
	elif mode == 'modalities':
		context['modalities'] = Modality.objects.filter(dataset = dataset).order_by('-terms_count')
	elif mode == 'settings':
		context['settings'] = {'modalities': Modality.objects.filter(dataset = dataset)}
	elif mode == 'assessment':
		from assessment.models import AssessmentProblem, AssessmentTask, ProblemAssessor	
		assessment_types = settings.ASSESSMENT_TYPES
		context['assessment'] = dict()
		
		if request.user == dataset.owner:
			supervised_problems = AssessmentProblem.objects.filter(dataset=dataset)
			supervised_problems_send = []
			problems_to_create = assessment_types
			for problem in supervised_problems:
				if problem.type in problems_to_create: 
					problems_to_create.remove(problem.type)				
			context['assessment']['supervised_problems'] = supervised_problems
			context['assessment']['problems_to_create'] = problems_to_create			
		context['assessment']['problems_to_assess'] = ProblemAssessor.objects.filter(assessor=request.user,problem__dataset=dataset)
	elif mode == 'docs':
		docs = Document.objects.filter(dataset = dataset)
		if "search" in request.GET and len(search_query) >= 2: 
			context['documents'] = docs.filter(title__icontains = search_query) 
			context['search'] = True
		else:	
			context['documents'] = True
			
	
	context['models'] = ArtmModel.objects.filter(dataset = dataset)
	try:
		context['active_model'] = ArtmModel.objects.get(id=request.COOKIES["model_" + str(dataset.id)])
	except:
		pass
	return render(request, 'datasets/dataset.html', Context(context)) 
	

	
import numpy as np
from scipy.spatial.distance import euclidean, cosine
def visual_document(request): 
	if 'id' in request.GET:
		document = Document.objects.get(id = request.GET['id'])
		dataset = document.dataset
	else:
		dataset = Dataset.objects.get(text_id = request.GET['dataset'])
		document = Document.objects.get(dataset = dataset, index_id = int(request.GET['iid']))
	
	try:
		mode = request.GET['mode']
	except:
		mode = 'text'
	
	context = {'document': document, 'mode': mode}
	
	# Detemine model - from request get parameter model_id, or from cookies
	model = None
	if "model_id" in request.GET:	
		try:
			model = ArtmModel.objects.get(id = request.GET["model_id"])  
		except:
			pass
	else:
		key = "model_" + str(dataset.id)
		if key in request.COOKIES and not "mode" in request.GET:
			return redirect("/document?id=" + str(document.id) + "&mode=" + mode + "&model_id=" + request.COOKIES[key])
	
	context["model"] = model
	
	if mode == 'all_topics':
		topics_count = [int(x) for x in model.topics_count.split()] 
		target_layer = model.layers_count
		theta = model.get_theta()
		topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("index_id")
		shift = 0
		for i in range(1, target_layer):
			shift += topics_count[i]
		topics_list = []
		for topic_index_id in range(0, topics_count[target_layer]):
			topics_list.append((theta[shift + topic_index_id, document.index_id - 1], topic_index_id))
		topics_list.sort(reverse = True)
		context['topics'] = [{"weight": 100*i[0], "topic": topics_index[i[1]]} for i in topics_list]
		return render(request, 'datasets/document_all_topics.html', Context(context)) 
 	
	
	context['tags'] = document.fetch_tags()
	context['models'] = ArtmModel.objects.filter(dataset=dataset)

	# Topics distribution in document (actually, column form Theta)
	if not model is None:
		topics_count = [int(x) for x in model.topics_count.split()]
		target_layer = model.layers_count
		phi = model.get_phi()
		theta = model.get_theta()
		theta_t = theta.transpose()
		documents_count = dataset.documents_count
		
		hl_topics = [0 for i in range(0, topics_count[target_layer])]
		topics = []
		topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("index_id")
		shift = 0
		for i in range(1, target_layer):
			shift += topics_count[i]
		topics_list = []
		document_matrix_id = document.index_id - 1
		for topic_index_id in range(0, topics_count[target_layer]):
			topics_list.append((theta[shift + topic_index_id, document_matrix_id], topic_index_id))
		topics_list.sort(reverse = True) 
		
		topics = []
		idx = 0
		other_weight = 1
		for (weight, topic_index_id) in topics_list:
			if other_weight < 0.05:
				break
			idx +=1  
			topic = topics_index[topic_index_id] 
			hl_topics[topic.index_id] = idx
			other_weight -= weight
			topics.append({
				"i" : idx, 
				"title": topic.title, 
				"weight": weight,  
				"url": "/topic?id=" + str(topic.id),
			})
		
		topics.append({
				"i" : 0, 
				"title": "Other", 
				"weight": other_weight,  
				"url": "/document?mode=all_topics&id=" + str(document.id) + "&model_id=" + str(model.id), 
			})
		context['topics'] = topics
	


		
	if mode  == 'bow':
		cut_bow = 1
		if "cut_bow" in request.COOKIES:
			cut_bow = int(request.COOKIES["cut_bow"])
		context['bow'] = document.fetch_bow(cut_bow)
	elif mode == 'text':		
		text = document.get_text()
		
		wi = document.get_word_index()
		highlight_terms = True
		if ("highlight_terms" in request.COOKIES and request.COOKIES["highlight_terms"] == "false") or not wi:
			highlight_terms = False
		 
		# Word highlight
		if highlight_terms:
			print(highlight_terms)
			if not model is None: 
				phi_layer = phi[:, shift : shift + topics_count[target_layer]]
				theta_t_layer = theta_t[document_matrix_id, shift : shift + topics_count[target_layer]]
			
			entries = []
			

			for start_pos, length, term_index_id in wi:
				if model is None:
					entries.append((start_pos, length, term_index_id, 0)) 
				else:
					term_matrix_id = term_index_id - 1
					topic_id = np.argmax(phi_layer[term_matrix_id] * theta_t_layer)	
					if phi_layer[term_matrix_id][topic_id] < 1e-9:
						# If term wasn't included to model
						class_id = -1
					else:
						class_id = hl_topics[topic_id]
					entries.append((start_pos, length, term_index_id, class_id)) 
		
			new_text = ""
			cur_pos = 0
			text_length = len(text)
			for (start_pos, length, term_index_id, class_id) in entries:
				if (cur_pos < start_pos):
					new_text += text[cur_pos : start_pos]
					cur_pos = start_pos
				new_text += "<a href = '/term?ds=" + str(dataset.id) + "&iid=" + str(term_index_id) + "' class = 'nolink tpc" + str(class_id) + "'>"
				new_text += text[cur_pos : cur_pos + length]
				new_text += "</a>"
				cur_pos += length
			
			if (cur_pos < text_length):
				new_text += text[cur_pos : text_length]
				cur_pos = text_length
			text = new_text
				
		context['lines'] = text.split('\n') 
			
		
	# Related documents 
	if not model is None:
		documents_index = Document.objects.filter(dataset = dataset).order_by("index_id")
		dist = np.zeros(documents_count)
		self_distr = theta_t[document_matrix_id]
		for other_document_id in range(0, documents_count):
			dist[other_document_id] = euclidean(self_distr, theta_t[other_document_id])
		
		idx = np.argsort(dist)[1:21]		
		context['related_documents'] = [documents_index[int(i)] for i in idx] 
					 
	response = render(request, 'datasets/document.html', Context(context))
	if "model_id" in request.GET:
		response.set_cookie("model_" + str(dataset.id), request.GET["model_id"])
	return response 
	
	
	
def visual_term(request):
	if "id" in request.GET:
		term = Term.objects.filter(id = request.GET['id'])[0]
	else:
		dataset = Dataset.objects.filter(id = request.GET['ds'])[0]
		term = Term.objects.filter(dataset = dataset, index_id = request.GET['iid'])[0]
	
	try:
		model = ArtmModel.objects.get(id = request.GET["model_id"])  
	except:
		model = None
	
	context = {'term': term, 'model': model}
	context['models'] = ArtmModel.objects.filter(dataset=term.dataset)
	term.count_documents_index()
	
	# Get distribution over topics (row from phi)
	if model:
		topics_count = [int(x) for x in model.topics_count.split()]
		shift = 0
		for i in range(1, model.layers_count):
			shift += topics_count[i]
		
		phi_row = model.get_phi()[term.index_id - 1]
		
		total_weight = 0
		topics = []
		topics_list = []
		topics_index = Topic.objects.filter(model = model, layer = model.layers_count).order_by("index_id")
		
		for topic_index_id in range(0, topics_count[model.layers_count]):
			topics_list.append((phi_row[shift + topic_index_id], topic_index_id))
			total_weight += phi_row[shift + topic_index_id]
		topics_list.sort(reverse = True) 
		
		for (weight, topic_index_id) in topics_list:
			topics.append({
				"topic": topics_index[topic_index_id], 
				"weight": weight,
				"show": (weight >= 0.05 * total_weight)
			})
		context['topics'] = topics
	
	return render(request, 'datasets/term.html', Context(context)) 
	
	
def visual_modality(request): 
	modality = Modality.objects.filter(id = request.GET['id'])[0]
	context = {"modality": modality}
	context["terms"] = Term.objects.filter(modality = modality).order_by("-token_tf")[:100]
	return render(request, 'datasets/modality.html', Context(context)) 
	
def global_search(request):
	context = {}
	if "search" in request.GET:
		search_query = request.GET["search"]
		context['search_query'] = search_query
		
		context['message'] = "Nothing found."
		total_found = 0
		if len(search_query) < 3:
			context['message'] = "Query is too short."
		else:
			documents = Document.objects.filter(title__icontains = search_query) 
			if len(documents) !=0:
				context["documents"] = documents
				total_found += len(documents)
				
			terms = Term.objects.filter(text__icontains = search_query) 
			if len(terms) != 0:
				context["terms"] = terms
				total_found += len(terms)
		
		if total_found > 0:
			context['message'] = "Found " + str(total_found) + " results."
		
	return render(request, 'datasets/search.html', Context(context))