from django.shortcuts import render, render_to_response
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound
from datasets.models import Dataset, Document
from models.models import ArtmModel
from visual.views import get_model
 
def datasets_list(request): 
	current_user = request.user
	entries = Dataset.objects.filter(owner__isnull = True)
	if request.user.is_authenticated == True:
		entries |= Dataset.objects.filter(owner = current_user)
	template = loader.get_template('datasets/datasets_list.html')
	context = Context({'entries': entries, 
					   'user': current_user})
	return HttpResponse(template.render(context)) 
	
	
def	datasets_reload(request):	
	try:
		dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	except:
		return redirect("/")
		
	dataset.reload()
	return HttpResponse("Reloaded. <a href ='/visual/dataset?dataset=" + dataset.text_id + "'> Return to dataset</a>.") 
	
	
def visual_dataset(request): 
	template = loader.get_template('datasets/dataset.html')
	try:
		target_dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	except:
		return redirect("/")
	
	docs = Document.objects.filter(dataset = target_dataset)
	models = ArtmModel.objects.filter(dataset = target_dataset)
	
	
	context = Context({'dataset': target_dataset,
					   'documents' : docs,
					   'models' : models,
					   'active_model' : get_model(request, target_dataset)
					   })
	return HttpResponse(template.render(context)) 
	
