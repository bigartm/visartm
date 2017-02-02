from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from datasets.models import Dataset, Document, Term, TermInDocument, Modality
from models.models import ArtmModel
from visual.views import get_model
import os
from django.conf import settings
import visartm.views as general_views
from threading import Thread
from datetime import datetime
 
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
			'minimal_length' : request.POST['minimal_length']
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
		dataset = Dataset.objects.get(text_id = request.POST['dataset'])
		dataset.name = request.POST['name']
		dataset.description = request.POST['description']
		dataset.preprocessing_params = request.POST['preprocessing_params']	
		dataset.is_public = ("is_public" in request.POST)
		dataset.save() 
		return redirect("/dataset/?dataset=" + request.POST['dataset'] + "&mode=settings")
	
	
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
		from django.contrib.auth.models import User
		
		assessment_types = ['segments']
		context['assessment'] = dict()
		
		if request.user == dataset.owner:
			supervised_problems = AssessmentProblem.objects.filter(dataset=dataset)
			supervised_problems_send = []
			problems_to_create = assessment_types
			for problem in supervised_problems:
				problems_to_create.remove(problem.type)
				not_assessors = [x.username for x in User.objects.all()]
				assessors = [x.assessor.username for x in ProblemAssessor.objects.filter(problem = problem)]
				for assessor in assessors:
					not_assessors.remove(assessor)
				supervised_problems_send.append({
					"problem": problem,
					"assessors": assessors,
					"not_assessors": not_assessors,
				})
				
			context['assessment']['supervised_problems'] = supervised_problems_send
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
	context['active_model'] = get_model(request, dataset)
	return render(request, 'datasets/dataset.html', Context(context)) 
	
	
def visual_term(request):
	if "id" in request.GET:
		term = Term.objects.filter(id = request.GET['id'])[0]
	else:
		dataset = Dataset.objects.filter(id = request.GET['ds'])[0]
		term = Term.objects.filter(dataset = dataset, index_id = request.GET['iid'])[0]
	context = {'term': term}
	term.count_documents_index()
	
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