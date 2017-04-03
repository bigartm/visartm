from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from datasets.models import Dataset, Document, Term, Modality
from models.models import ArtmModel, Topic
from django.conf import settings
import visartm.views as general_views
from threading import Thread
from datetime import datetime
from django.contrib.auth.decorators import login_required, permission_required
import os
from django.contrib.auth.models import User	
 
def datasets_list(request):  
	datasets = Dataset.objects.filter(is_public = True)
	if request.user.is_authenticated == True:
		datasets |= Dataset.objects.filter(owner = request.user) 
		
	context = Context({'datasets': datasets})
	return render(request, 'datasets/datasets_list.html', context)
	
@login_required	
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
	
@login_required
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

@login_required
@permission_required('datasets.add_dataset')
def	dataset_create(request):	
	if request.method == 'GET': 
		existing_datasets = [dataset.text_id for dataset in Dataset.objects.all()]
		folders = os.listdir(os.path.join(settings.DATA_DIR, "datasets"))
		unreg = [i for i in folders if (not i in existing_datasets) and (not i[0]=='.')]
		 
		context = Context({
			'unreg': unreg,
			'languages': settings.LANGUAGES
		})
		if settings.DEBUG:
			context['DEBUG'] = True
		return render(request, "datasets/create_dataset.html", context) 
	
	dataset = Dataset()
	if request.POST['mode'] == 'upload':
		name = str(request.FILES['archive']).split('.')[0]
		if len(Dataset.objects.filter(text_id = name)) != 0:
			return HttpResponseForbidden("Dataset %s already exists. Try another name." % name)
		dataset.upload_from_archive(request.FILES['archive'])
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
		t = Thread(target = Dataset.reload_untrusted, args = (dataset, ), daemon = True)
		t.start()
	else:
		dataset.reload()
	
	return redirect("/dataset?dataset=" + dataset.text_id) 
	
	
from django.conf import settings
def visual_dataset(request):  
	if request.method == "POST":
		dataset = Dataset.objects.get(text_id = request.POST['dataset'])
		if request.user != dataset.owner:
			return HttpResponseForbidden("You are not the owner.")
		dataset.name = request.POST['name']
		dataset.description = request.POST['description']
		dataset.preprocessing_params = request.POST['preprocessing_params']	
		dataset.is_public = ("is_public" in request.POST)
		dataset.language = request.POST['language']
		dataset.save() 
		return redirect("/dataset?dataset=" + request.POST['dataset'] + "&mode=settings")
	
	
	dataset = Dataset.objects.get(text_id = request.GET['dataset'])
	if dataset.status == 1:
		return general_views.wait(request, dataset.read_log() + \
			"<br><a href = '/datasets/reload?dataset=" + dataset.text_id + "'>Reload</a>", dataset.creation_time)
	elif dataset.status == 2:
		return general_views.message(request, dataset.error_message.replace("\n","<br>") + \
			"<br><a href = '/datasets/reload?dataset=" + dataset.text_id + "'>Reload</a>"+ \
			"<br><a href='/datasets/delete?id=" + str(dataset.id) + "'>Delete</a>")
	
	context = {'dataset': dataset}
	
	if "search" in request.GET:
		search_query = request.GET["search"]
		context['search_query'] = search_query
	
	mode = 'docs'
	if 'mode' in request.GET:
		mode = request.GET['mode'] 
		
	if mode == 'terms': 
		terms = Term.objects.filter(dataset = dataset) 
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
		for term in terms:
			y = term.token_tf
			if y != last_y:
				word.append(x)
				freq.append(y)
				last_y = y 
			x+=1	
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
		context['settings'] = {
			'modalities': Modality.objects.filter(dataset = dataset),
			'languages': ['english', 'russian', 'ukrainian']
		}
	elif mode == 'assessment':
		from assessment.models import AssessmentProblem, AssessmentTask, ProblemAssessor	
		context['assessment'] = {}
		if request.user == dataset.owner:
			supervised_problems = AssessmentProblem.objects.filter(dataset=dataset)
			assessment_folders = os.listdir(os.path.join(settings.BASE_DIR, "templates", "assessment"))
			problems_to_create = [x for x in assessment_folders if not '.' in x]
			#for problem in supervised_problems:
			#	if problem.type in problems_to_create: 
			#		problems_to_create.remove(problem.type)				
			context['assessment']['supervised_problems'] = supervised_problems
			context['assessment']['problems_to_create'] = problems_to_create		
	
		try:
			context['assessment']['problems_to_assess'] = ProblemAssessor.objects.filter(assessor=request.user,problem__dataset=dataset)
		except:
			context['assessment']['problems_to_assess'] = []
			
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
	

	
def document_all_topics(request):
	document = Document.objects.get(id = request.GET['id'])
	model = ArtmModel.objects.get(id = request.GET["model_id"])  
	context = {}
	
	topics_count = [int(x) for x in model.topics_count.split()] 
	target_layer = model.layers_count
	theta = model.get_theta()
	topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("index_id")
	shift = 0
	for i in range(1, target_layer):
		shift += topics_count[i]
	topics_list = []
	for topic_index_id in range(0, topics_count[target_layer]):
		topics_list.append((theta[shift + topic_index_id, document.index_id], topic_index_id))
	topics_list.sort(reverse = True)
	context['topics'] = [{"weight": 100*i[0], "topic": topics_index[i[1]]} for i in topics_list]
	return render(request, 'datasets/document_all_topics.html', Context(context)) 
	
	
	
import numpy as np
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
		
 	
	
	context['tags'] = document.fetch_tags()
	context['models'] = ArtmModel.objects.filter(dataset=dataset)

	# Topics distribution in document (actually, column form Theta)
	if not model is None:
		topics_count = [int(x) for x in model.topics_count.split()]
		target_layer = model.layers_count
		phi = model.get_phi()
		theta = model.get_theta()
		theta_t = theta.transpose()
		
 
		topics_index = Topic.objects.filter(model = model, layer = target_layer).order_by("index_id")
			
	
		hl_topics = [0 for i in range(0, topics_count[target_layer])]
		topics_list = [] 
		
	 
		shift = 0
		for i in range(1, target_layer):
			shift += topics_count[i]
		
		for topic_index_id in range(0, topics_count[target_layer]):
			topics_list.append((theta[shift + topic_index_id, document.index_id], topic_index_id))
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
				"url": "/datasets/document_all_topics?id=" + str(document.id) + "&model_id=" + str(model.id), 
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
			if not model is None: 
				phi_layer = phi[:, shift : shift + topics_count[target_layer]]
				theta_t_layer = theta_t[document.index_id, shift : shift + topics_count[target_layer]]
		
				entries = []
				

				for start_pos, length, term_index_id in wi:
					class_id=0
					topic_id = np.argmax(phi_layer[term_index_id] * theta_t_layer)	
					if phi_layer[term_index_id][topic_id] < 1e-9:
						# If term wasn't included to model
						class_id = -1
					else:
						class_id = hl_topics[topic_id]
					entries.append((start_pos, length, term_index_id, class_id)) 
			else:
				entries = [(start_pos, length, term_index_id, 0) for start_pos, length, term_index_id in wi]
			
			
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
		context['related_documents'] = model.get_related_documents(document.index_id)
		context['segmentation_available'] = model.segmentation_available(document)
					 
	response = render(request, 'datasets/document.html', Context(context))
	if "model_id" in request.GET:
		response.set_cookie("model_" + str(dataset.id), request.GET["model_id"])
	return response 
	
def document_segments(request):
	document = Document.objects.get(id = request.GET['id'])
	model = ArtmModel.objects.get(id = request.GET['model_id'])
	context = {"document" : document, "model" : model}
	
	
	#First, build topic list
	segments = model.get_segmentation(document)
	if not segments:
		return general_views.message(request, "Bad segments file.")
	topics_index_id_set = set([int(x[2]) for x in segments])
	topics_index = model.get_topics()
	class_index = {}
	topics_list = []
	
	class_id = 0
	for topic_index_id in topics_index_id_set:
		class_id += 1
		topic = topics_index[topic_index_id]
		topics_list.append(topic)
		class_index[topic_index_id] = class_id
	
	new_text = ""
	cur_pos = 0
	for start_index, end_index, topic_index_id in segments:
		new_text += "%s<span class='tpc%d'>%s</span>" % (
			document.text[int(cur_pos) : int(start_index)], 
			class_index[int(topic_index_id)], 
			document.text[int(start_index) : int(end_index)]
		)
		cur_pos = end_index
	new_text += document.text[int(cur_pos) :]
	
	context["text"] = new_text.split("\n")
	context["topics_count"] = len(topics_list)
	context["topics"] = topics_list
	
	
	
	text_result = 0
	
	return render(request, 'datasets/document_segments.html', Context(context))
	
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
	
	# Get distribution over topics (row from phi)
	if model:
		topics_count = [int(x) for x in model.topics_count.split()]
		shift = 0
		for i in range(1, model.layers_count):
			shift += topics_count[i]
		
		phi_row = model.get_phi()[term.index_id]
		
		total_weight = 0
		topics = []
		topics_list = []
		topics_index = Topic.objects.filter(model = model, layer = model.layers_count).order_by("index_id")
		
		for topic_index_id in range(0, topics_count[model.layers_count]):
			topics_list.append((phi_row[shift + topic_index_id], topic_index_id))
			total_weight += phi_row[shift + topic_index_id]
		topics_list.sort(reverse = True) 
		
		weight_sum = 0
		for (weight, topic_index_id) in topics_list:
			topics.append({
				"topic": topics_index[topic_index_id], 
				"weight": weight,
				"show": (weight >= 0.05 * total_weight)
			})
			weight_sum += weight
		
		context['topics'] = topics
		if weight_sum == 0:
			context['topics_all_zeros'] = True
	
	term.count_documents_index()
	return render(request, 'datasets/term.html', Context(context)) 
	
	
def visual_modality(request): 
	modality = Modality.objects.filter(id = request.GET['id'])[0]
	context = {"modality": modality}
	context["terms"] = Term.objects.filter(modality = modality).order_by("-token_tf")[:100]
	return render(request, 'datasets/modality.html', Context(context)) 
	
def dump(request):
	dataset = Dataset.objects.get(id = request.GET['dataset_id'])
	import zipfile
	import io
	 
	
	
	outfile = io.BytesIO()
	folder = dataset.get_folder()
	with zipfile.ZipFile(outfile, 'w') as zf:
		for root, dirs, files in os.walk(folder):
			if "batches" in root or "_MACOSX" in root:
				continue
			rel_path = root[len(folder)+1:]
			for file in files:
					if file[0] == '.':
						continue
					if 'models' in root and '.' in file and (not file[:-4] == '.txt'):
						continue
					zf.write(os.path.join(root, file), os.path.join(rel_path, file)) 

	zipped_file = outfile.getvalue()
	response = HttpResponse(zipped_file, content_type='application/octet-stream')
	response['Content-Disposition'] = 'attachment; filename=%s.zip' % dataset.text_id 
	return response

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
			documents_file_name = Document.objects.filter(text_id__icontains = search_query) 
			context["documents_file_name"] = documents_file_name
			total_found += len(documents_file_name)
			
			documents_title = Document.objects.filter(title__icontains = search_query) 
			context["documents_title"] = documents_title
			total_found += len(documents_title)
			
			terms = Term.objects.filter(text__icontains = search_query) 
			if len(terms) != 0:
				context["terms"] = terms
				total_found += len(terms)
		
			accounts = User.objects.filter(username__icontains=search_query)
			if len(accounts) != 0:
				context["accounts"] = accounts
				total_found += len(accounts)
				
			parsed = search_query.split()
			if len(parsed) > 1:
				query_length = len(parsed)
				terms_try = Term.objects.filter(text=parsed[0])
				documents = []
				for term in terms_try:
					try:
						other_terms = [Term.objects.get(dataset=term.dataset, text=parsed[i]).index_id for i in range(1, query_length)]
					except:
						continue
					conc = [term.index_id] + other_terms	
						
					for document in term.get_documents():
						match = True
						for iid in other_terms:
							if document.count_term(iid)==0:
								match = False
						if match:
							documents.append({
								"document": document,
								"concordance" : document.get_concordance(conc)
							})
		
				if len(documents) != 0:
					context["documents"] = documents
					total_found += len(documents)
		
		if total_found > 0:
			context['message'] = "Found " + str(total_found) + " results."
		
	return render(request, 'datasets/search.html', Context(context))