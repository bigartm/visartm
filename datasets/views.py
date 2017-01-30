from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound
from datasets.models import Dataset, Document, Term, TermInDocument, Modality
from models.models import ArtmModel
from visual.views import get_model
import os
from django.conf import settings
import visartm.views as general_views
from threading import Thread
from datetime import datetime
 
def datasets_list(request): 
	current_user = request.user
	datasets = Dataset.objects.filter(owner__isnull = True)
	if request.user.is_authenticated == True:
		datasets |= Dataset.objects.filter(owner = current_user) 
		
	context = Context({'datasets': datasets, 
					   'user': current_user})
	return render(request, 'datasets/datasets_list.html', context)
	
	
def	datasets_reload(request):	
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	dataset.status = 1
	dataset.creation_time = datetime.now()
	dataset.save()	
	
	if settings.CONSOLE_OUTPUT:
		dataset.reload()
	else:
		t = Thread(target = Dataset.reload_untrusted, args = (dataset, ), daemon = True)
		t.start()
	
	return redirect("/dataset?dataset=" + dataset.text_id) 
	
	
def	datasets_create(request):	
	if request.method == 'GET': 
		existing_datasets = [dataset.text_id for dataset in Dataset.objects.all()]
		folders = os.listdir(os.path.join(settings.DATA_DIR, "datasets"))
		unreg = [i for i in folders if not i in existing_datasets]
		 
		context = Context({"unreg": unreg})
		return render(request, "datasets/create_dataset.html", context) 
	
	print(request.POST)
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
		}
	import json
	dataset.preprocessing_params = json.dumps(preprocessing_params)	
	#return HttpResponse(dataset.preprocessing_params)
	
	
	dataset.owner = request.user  
	if not dataset.check_can_load():
		return HttpResponse(dataset.error_message)
	dataset.status = 1
	dataset.creation_time = datetime.now()	
	dataset.save()	
	
	t = Thread(target = Dataset.reload, args = (dataset, ), daemon = True)
	t.start()
	
	return redirect("/dataset?dataset=" + dataset.text_id) 
	
	
def visual_dataset(request):  
	if request.method == "POST":
		print(request.POST)
		dataset = Dataset.objects.filter(text_id = request.POST['dataset'])[0]
		dataset.name = request.POST['name']
		dataset.description = request.POST['description']
		dataset.preprocessing = request.POST['preprocessing']
		
		dataset.save() 
		return redirect("/dataset/?dataset=" + request.POST['dataset'] + "&mode=settings")
	
	
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
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
		else:	
			terms = terms.order_by("-token_tf")[:100] 
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
	elif mode == 'docs':
		docs = Document.objects.filter(dataset = dataset)
		if "search" in request.GET and len(search_query) >= 2: 
			docs = docs.filter(title__icontains = search_query) 
		else:	
			docs = docs[:100] 
		context['documents'] = docs
	
	context['models'] = ArtmModel.objects.filter(dataset = dataset)
	context['active_model'] = get_model(request, dataset)
	return render(request, 'datasets/dataset.html', Context(context)) 
	
	
def visual_term(request):
	if "id" in request.GET:
		term = Term.objects.filter(id = request.GET['id'])[0]
	else:
		dataset = Dataset.objects.filter(id = request.GET['ds'])[0]
		term = Term.objects.filter(dataset = dataset, index_id = request.GET['iid'])[0]
	context = {'term': term}
	
	if "docs" in request.GET and request.GET["docs"] == "true":
		term.count_documents_index()
		#return HttpResponse("FFF")
		context["docs"] = TermInDocument.objects.filter(term = term).order_by("-count")
		print(context["docs"])
	
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