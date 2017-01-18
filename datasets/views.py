from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound
from datasets.models import Dataset, Document, Term
from models.models import ArtmModel
from visual.views import get_model
import os
from django.conf import settings
import artmonline.views as general_views
from threading import Thread
from datetime import datetime
 
def datasets_list(request): 
	current_user = request.user
	entries = Dataset.objects.filter(owner__isnull = True)
	if request.user.is_authenticated == True:
		entries |= Dataset.objects.filter(owner = current_user) 
		
	context = Context({'entries': entries, 
					   'user': current_user})
	return render(request, 'datasets/datasets_list.html', context)
	
	
def	datasets_reload(request):	
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	dataset.status = 1
	dataset.creation_time = datetime.now()
	dataset.save()	
	
	t = Thread(target = Dataset.reload, args = (dataset, ), daemon = True)
	t.start()
	
	return redirect("/dataset?dataset=" + dataset.text_id) 
	
	
def	datasets_create(request):	
	if request.method == 'GET': 
		existing_datasets = [dataset.text_id for dataset in Dataset.objects.all()]
		folders = os.listdir(os.path.join(settings.DATA_DIR, "datasets"))
		unreg = [i for i in folders if not i in existing_datasets]
		
		languages = ['undefined', 'russian', 'english'] 
		context = Context({"languages": languages,
						   "unreg": unreg})
		return render(request, "datasets/create_dataset.html", context) 
	
	print(request.POST)
	dataset = Dataset()
	dataset.name = request.POST['unreg_name']
	dataset.text_id = dataset.name
	dataset.description = request.POST['description']
	dataset.owner = request.user
	if 'time_provided' in request.POST:
		dataset.time_provided = True
	if 'text_provided' in request.POST:
		dataset.text_provided = True
	if 'word_index_provided' in request.POST:
		dataset.word_index_provided = True
	if 'uci_provided' in request.POST:
		dataset.uci_provided = True
	if 'json_provided' in request.POST:
		dataset.json_provided = True
	dataset.language = request.POST['lang']
	if not dataset.check_can_load():
		return HttpResponse(dataset.error_message)
	dataset.status = 1
	dataset.creation_time = datetime.now()
	dataset.save()	
	
	t = Thread(target = Dataset.reload, args = (dataset, ), daemon = True)
	t.start()
	
	return redirect("/dataset?dataset=" + dataset.text_id) 
	
	
def visual_dataset(request):  
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	
	if dataset.status != 0:
		return general_views.wait(request, dataset.read_log(), dataset.creation_time)
	
	docs = Document.objects.filter(dataset = dataset)
	
	search_query = ""
	if "search" in request.GET:
		search_query = request.GET["search"]
		docs = docs.filter(title__contains = search_query)
		
		
	docs = docs[:100]
	models = ArtmModel.objects.filter(dataset = dataset)
	
	
	context = Context({'dataset': dataset,
					   'documents' : docs,
					   'models' : models,
					   'active_model' : get_model(request, dataset),
					   'search_query' : search_query,
					   })
					   
	return render(request, 'datasets/dataset.html', context) 
	
	
def visual_term(request):
	dataset = Dataset.objects.filter(id = request.GET['ds'])[0]
	term = Term.objects.filter(dataset = dataset, index_id = request.GET['iid'])[0]
	return render(request, 'datasets/term.html', Context({'term': term})) 
	
	
	