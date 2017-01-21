from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound
from datasets.models import Dataset, Document, Term, TermInDocument
from models.models import ArtmModel
from visual.views import get_model
import os
from django.conf import settings
import artmonline.views as general_views
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
	
	t = Thread(target = Dataset.reload_untrusted, args = (dataset, ), daemon = True)
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
	if request.POST['mode'] == 'upload':
		dataset.upload_from_archive(request.FILES['archive'])
		#return HttpResponse("OK")
	else:
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
	
	if dataset.status == 1:
		return general_views.wait(request, dataset.read_log() + \
			"<br><a href = '/datasets/reload?dataset=" + dataset.text_id + "'>Reload</a>", dataset.creation_time)
	elif dataset.status == 2:
		return general_views.message(request, dataset.error_message.replace("\n","<br>") + \
			"<br><a href = '/datasets/reload?dataset=" + dataset.text_id + "'>Reload</a>")
	
	
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
	
	return render(request, 'datasets/term.html', Context(context)) 
	
	
	