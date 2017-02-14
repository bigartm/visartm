from django.shortcuts import render, redirect
from datasets.models import Dataset, Modality, Term
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from models.models import ArtmModel, Topic, TopicRelated, TopicInTopic, TopTerm
from visual.models import GlobalVisualization
from django.contrib.auth.decorators import login_required, permission_required
import visartm.views as general_views
import traceback
from django.conf import settings
import os
from threading import Thread
from datetime import datetime
import numpy as np

def visual_model(request):
	model = ArtmModel.objects.get(id = request.GET['model'])
		
	if model.status != 0:
		if model.status == 1:
			return general_views.wait(request, model.read_log(), model.creation_time)
		if model.status == 2:
			return general_views.message(request, 
				"Model is bad. Error occured.<br>" + 
				model.error_message.replace('\n',"<br>") + "<br>" +
				"<a href = '/models/delete_model?model=" + str(model.id) + "'>Delete this model</a><br>" +
				"<a href = '/models/reload_model?model=" + str(model.id) + "'>Reload this model</a><br>" )
		if model.status == 3:
			return general_views.message(request, 
				"This is empty model.<br>" +
				"Place matrices in folder " + model.get_folder() + "<br>"
				"Then <a href='/models/reload_model?model=" + str(model.id) + "'>reload model</a>.")
		
	topics_count = model.topics_count.split()
	topics = Topic.objects.filter(model = model)
	topics_layers = [{"i": i + 1, "topics_count": topics_count[i+1], \
			"topics": topics.filter(layer = i + 1).order_by("spectrum_index")} for i in range (0, model.layers_count)]
	template = loader.get_template('models/model.html')
	context = Context({'model': model, 'topics_layers' : topics_layers})
	return render(request, 'models/model.html', context) 

@login_required
def reload_model(request):
	try:
		model = ArtmModel.objects.get(id = request.GET['model'])
	except:
		model = ArtmModel.objects.get(id = request.GET['id'])
	
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author")
	
	if model.status == 1:
		return general_views.message(request, "Model is locked.")
	model.creation_time = datetime.now()
	model.status = 1
	model.save()
	model.prepare_log()
	
	t = Thread(target = ArtmModel.reload_untrusted, args = (model, ), daemon = True)
	t.start()
	
	return redirect("/model?model=" + str(model.id))

@login_required
def arrange_topics(request):
	model = ArtmModel.objects.get(id = request.GET['model'])
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author")
	if model.status != 0:
		return general_views.message(request, "Model is locked.")
	model.creation_time = datetime.now()
	model.status = 1
	model.save()
	model.prepare_log()
	
	t = Thread(target = ArtmModel.arrange_topics, args = (model, request.GET['mode'],), daemon = True)
	t.start()
	
	return redirect("/model?model=" + str(model.id))

@login_required
def reset_visuals(request):
	model = ArtmModel.objects.get(id=request.GET['model'])
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author")
	GlobalVisualization.objects.filter(model = model).delete()
	return general_views.message(request, "Resetted. <a href ='/model?model=" + str(model.id) + "'> <br>Return to model</a>.") 

@permission_required("add_artmmodel")
@login_required
def create_model(request):
	if request.method == 'GET': 
		dataset = Dataset.objects.get(text_id=request.GET['dataset'])
		if not dataset.check_access(request.user):
			return HttpResponceForbidden("You have not access to this dataset")
		modalities = Modality.objects.filter(dataset = dataset)
		scripts = os.listdir(os.path.join(settings.DATA_DIR, "scripts"))
		
		unreg = []
		try:
			folders = os.listdir(os.path.join(settings.DATA_DIR, "datasets", dataset.text_id, "models"))
			existing_models = [model.text_id for model in ArtmModel.objects.filter(dataset = dataset)]
			unreg = [i for i in folders if (not i in existing_models) and (not i[0] == '.')]
		except:
			pass
			
		context = Context({'dataset': dataset,
						   'modalities': modalities,
						   'scripts': scripts,
						   'unreg': unreg})
						   
		return render(request, 'models/create_model.html', context)
	
	#print(request.POST)
	dataset = Dataset.objects.get(text_id = request.POST['dataset'])
	if not dataset.check_access(request.user):
		return HttpResponceForbidden("You have not access to this dataset")
	model = ArtmModel()
	model.dataset = dataset
	model.name = request.POST['model_name']
	#model.main_modality = Modality.objects.filter(dataset = dataset, name = request.POST['word_modality'])[0]
	model.threshold = int(request.POST['threshold'])
	model.author = request.user
	model.creation_time = datetime.now()
	model.status = 1
	model.save()
	model.prepare_log()
	
	if settings.THREADING:
		t = Thread(target = ArtmModel.create_generic, args = (model, request.POST, ), daemon = True)
		t.start()
	else:
		model.create_generic(request.POST)
	
	
	return redirect("/model?model=" + str(model.id))
	
@login_required
def delete_model(request):
	model = ArtmModel.objects.get(id=request.GET['model'])
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author")
	dataset_name = model.dataset.text_id 
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author of the model.")
	if 'sure' in request.GET and request.GET['sure'] == 'yes': 
		ArtmModel.objects.filter(id = request.GET['model']).delete()
		return general_views.message(request, "Model was deleted. <a href ='/dataset?dataset=" + dataset_name + "'> Return to dataset</a>.")
	else:
		return general_views.message(request,
			"Are you sure that you want delete model " + str(model) + " permanently?<br>" + 
			"<a href = '/models/delete_model?model=" + str(model.id) + "&sure=yes'>Yes</a><br>" +
			"<a href = '/dataset?dataset=" + dataset_name + "'>No</a>")
	

@login_required
def delete_all_models(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	if request.user != dataset.owner:
		return HttpResponseForbidden("You are not the owner of the dataset.")
	if 'sure' in request.GET and request.GET['sure'] == 'yes': 
		ArtmModel.objects.filter(dataset = dataset).delete()
		return general_views.message(request, "All models were deleted. <a href ='/dataset?dataset=" + 
					dataset.text_id + "'>Return to dataset</a>.")
	else:
		return general_views.message(request, 
				"Are you sure that you want delete ALL models for dataset " + str(dataset) + " permanently?<br>" + 
				"<a href = '/models/delete_all_models?dataset=" + dataset.text_id + "&sure=yes'>Yes</a><br>" +
				"<a href = '/dataset?dataset=" + dataset.text_id + "'>No</a>")	
							
def	visual_topic(request):
	topic = Topic.objects.filter(id = request.GET['id'])[0]
	model = topic.model 
	related_topics = TopicRelated.objects.filter(model = topic.model, topic1 = topic).order_by("weight")	
	context = {'topic': topic, 'related_topics' : related_topics}
	
	 
	if 'mode' in request.GET and request.GET['mode'] == 'topterms':
		context['modalities'] = Modality.objects.filter(dataset=model.dataset)
		top_terms = TopTerm.objects.filter(topic=topic)
		if 'modality' in request.GET and request.GET['modality'] != 'all':
			modality = Modality.objects.get(dataset=model.dataset, name=request.GET["modality"])
			top_terms = top_terms.filter(term__modality=modality)
		top_terms=top_terms.order_by("-weight")
		context['top_terms'] = top_terms
	else:
		if topic.layer < model.layers_count:
			context['topics'] = TopicInTopic.objects.filter(parent = topic) 
		else:
			context['documents'] = True
			
	context['low_level'] = (topic.layer == model.layers_count)
	
	return render(request, 'models/topic.html', Context(context))
	
@login_required
def rename_topic(request):
	topic = Topic.objects.get(id = request.POST['id'])
	if request.user != topic.model.author:
		return HttpResponseForbidden("You are not the author of the model.")
	topic.rename(request.POST['new_title'])
	return redirect("/topic?id=" + request.POST['id'])	
