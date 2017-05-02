from django.shortcuts import render, redirect
from datasets.models import Dataset, Modality, Term
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from models.models import ArtmModel, Topic, TopicRelated, TopicInTopic, TopTerm
from django.contrib.auth.decorators import login_required, permission_required
import visartm.views as general_views
import traceback
from django.conf import settings
import os
from threading import Thread
from datetime import datetime
import numpy as np
import json
from models.bigartm_config import REGULARIZERS


def models_list(request):
	try:
		models = ArtmModel.objects.filter(author = request.user).order_by("id")
	except:
		models = []
		
	context = {"models": models}
	return render(request, 'models/models_list.html', context) 

def visual_model(request):
	model = ArtmModel.objects.get(id = request.GET['model'])
		
	if model.status != 0:
		if model.status == 1 or model.status == 11:
			return general_views.wait(request, model.read_log(), model.creation_time)
		if model.status == 2:
			return general_views.message(request, 
				"Model is bad. Error occured.<br>" + 
				model.error_message.replace('\n',"<br>") + "<br>" +
				"<a href = '/models/delete_model?model=" + str(model.id) + "'>Delete this model</a><br>" +
				"<a href = '/models/reload_model?model=" + str(model.id) + "'>Reload this model</a><br>" )
		if model.status == 3:
			return redirect('/models/settings?model_id=%d' % model.id) 
	
	if 'matrices' in request.GET:
		try:
			head = int(request.GET['matrices'])
		except:
			head = 10
		import pandas as pd
		ret = ""
		ret += "MATRIX PHI<br>"
		ret += pd.read_pickle(os.path.join(model.get_folder(), "phi"))[0:head].to_html() +  "<br>"
		
		phi = model.get_phi()
		for i in range(head):
			for j in range(phi.shape[1]):
				ret += ("%.05f " % phi[i][j])
			ret += "<br>"
			
		ret += "<br><br><br>MATRIX THETA<br>"
		ret += pd.read_pickle(os.path.join(model.get_folder(), "theta"))[0:head].to_html()
		
		theta = model.get_theta()
		for i in range(min(theta.shape[0],head)):
			for j in range(min(theta.shape[1],head)):
				ret += ("%.02e " % theta[i][j])
			ret += "<br>"
		
		return HttpResponse(ret)
	
	topics_count = model.topics_count.split()
	topics = Topic.objects.filter(model = model)
	topics_layers = [{"i": i + 1, "topics_count": topics_count[i+1], \
			"topics": topics.filter(layer = i + 1).order_by("spectrum_index")} for i in range (0, model.layers_count)]
	template = loader.get_template('models/model.html')
	context = Context({'model': model, 'topics_layers' : topics_layers})
	from algo.metrics import metrics_list
	context["metrics"] = metrics_list
	return render(request, 'models/model.html', context) 

def model_log(request):
	model = ArtmModel.objects.get(id = request.GET['model_id'])
	return HttpResponse(model.read_log())
	
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
	model.status = 11
	model.save()
	model.prepare_log()
	
	mode = request.GET['mode']
	try:
		metric = request.GET['metric']
	except:
		metric = "default"
		
	if settings.THREADING:
		t = Thread(target = ArtmModel.arrange_topics, args = (model, mode, metric,), daemon = True)
		t.start()
	else:
		model.arrange_topics(mode, metric)
		
	return redirect("/model?model=" + str(model.id))

@login_required
def reset_visuals(request):
	model = ArtmModel.objects.get(id=request.GET['model'])
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author")
	model.reset_visuals()
	return general_views.message(request, "Resetted. <a href ='/model?model=" + str(model.id) + "'> <br>Return to model</a>.") 

@permission_required("models.add_artmmodel")
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
			
		context['regularizers'] = REGULARIZERS
			
		if settings.DEBUG:
			context['DEBUG'] = True
						   
		return render(request, 'models/create_model.html', context)
	
	#print(request.POST)

	
	dataset = Dataset.objects.get(text_id = request.POST['dataset'])
	if not dataset.check_access(request.user):
		return HttpResponceForbidden("You have not access to this dataset")
	model = ArtmModel()
	model.dataset = dataset
	model.name = request.POST['model_name']
	#model.main_modality = Modality.objects.filter(dataset = dataset, name = request.POST['word_modality'])[0]
	model.threshold_hier = int(request.POST['threshold_hier'])
	model.threshold_docs = int(request.POST['threshold_docs'])	
	model.author = request.user
	model.creation_time = datetime.now()
	model.status = 1
	model.save()
	#model.prepare_log()
	
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
		return HttpResponseForbidden("You are not the author! (<a href='/admin/models/artmmodel/%d/change/'>Delete as admin</a>)" % model.id)
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
						
def visual_topic(request):
	topic = Topic.objects.filter(id = request.GET['id'])[0]
	model = topic.model 
	related_topics = TopicRelated.objects.filter(model = topic.model, topic1 = topic).order_by("weight")	
	context = {'topic': topic, 'related_topics' : related_topics}
	
	if 'mode' in request.GET and request.GET['mode'] == 'phi_column':
		terms = Term.objects.filter(dataset=model.dataset).order_by('index_id')
		mod_index = dict()
		for modality in Modality.objects.filter(dataset=model.dataset):
			mod_index[modality.id] = modality.name
		
		ans = ""
		phi = model.get_phi()
		for term in terms:
			ans += "%s %s %f<br>" % (term.text, mod_index[term.modality_id], phi[term.index_id, topic.matrix_id])
		return HttpResponse(ans)
	
	if 'mode' in request.GET:
		mode = request.GET['mode']
	else:
		if (topic.layer == model.layers_count):
			mode = 'documents'
		else:
			mode = 'topics'
	
	if mode == 'topterms':
		context['modalities'] = Modality.objects.filter(dataset=model.dataset)
		top_terms = TopTerm.objects.filter(topic=topic)
		if 'modality' in request.GET and request.GET['modality'] != 'all':
			modality = Modality.objects.get(dataset=model.dataset, name=request.GET["modality"])
			top_terms = top_terms.filter(term__modality=modality)
		top_terms=top_terms.order_by("-weight")
		context['top_terms'] = top_terms
	elif mode == 'topics':
		context['topics'] = TopicInTopic.objects.filter(parent = topic) 
	elif mode == 'documents':
		context['documents'] = True
			
	context['low_level'] = (topic.layer == model.layers_count)
	context['mode'] = mode
	
	
	return render(request, 'models/topic.html', Context(context))
	
def dump_model(request):
	model = ArtmModel.objects.get(id=request.GET["model_id"])
	
	import zipfile
	import io
	
	outfile = io.BytesIO()
	folder = model.get_folder()
	with zipfile.ZipFile(outfile, 'w') as zf:
		files = ["theta", "phi"]
		files += [("psi%d" % i) for i in range(1, model.layers_count)]
		for file_name in files:
			zf.write(os.path.join(folder, file_name), file_name) 

	zipped_file = outfile.getvalue()
	response = HttpResponse(zipped_file, content_type='application/octet-stream')
	response['Content-Disposition'] = 'attachment; filename=%s_%s.zip' % (str(model.dataset), str(model))
	return response


	
def related_topics(request):
	topic = Topic.objects.get(id=request.GET["topic_id"])
	model = topic.model
	
	
	import algo.metrics as metrics
	if "metric" in request.GET:
		metric = request.GET["metric"]
	else:
		metric = metrics.default_metric
	
	context = {"topic": topic, "metrics": metrics.metrics_list, "metric": metric}
	context["topics"] = model.get_related_topics(topic, metric=metric)
	
	return render(request, 'models/related_topics.html', Context(context))
	
@login_required
def rename_topic(request):
	topic = Topic.objects.get(id = request.POST['id'])
	if request.user != topic.model.author:
		return HttpResponseForbidden("You are not the author of the model.")
	topic.rename(request.POST['new_title'])
	return redirect("/topic?id=" + request.POST['id'])	
	
@login_required
def model_settings(request):
	if request.method == 'POST':
		action = request.POST['action']
		model = ArtmModel.objects.get(id=request.POST['model_id'])
		if request.user != model.author:
			return HttpResponseForbidden("You are not the author.")
		
		if action == 'parameters':
			new_threshold_docs = int(request.POST['threshold_docs'])
			new_threshold_hier = int(request.POST['threshold_hier'])
			new_max_parents_hier = int(request.POST['max_parents_hier'])
			
			
			if new_threshold_docs != model.threshold_docs:
				model.threshold_docs = new_threshold_docs
				model.save()
				model.extract_docs()
				
			if new_threshold_hier != model.threshold_hier or new_max_parents_hier != model.max_parents_hier:
				model.threshold_hier = new_threshold_hier
				model.max_parents_hier = new_max_parents_hier
				model.save()
				model.build_hier() 
				
			model.reset_visuals()
		elif action == 'matrices':
			model.log("Archive uploaded.")
			archive = request.FILES['archive'] 
			from tools.views import get_temp_folder
			import zipfile
			
			with get_temp_folder() as folder:
				zip_file_name = os.path.join(folder, "a.zip")
				with open(zip_file_name, 'wb+') as f:
					for chunk in archive.chunks():
						f.write(chunk)
						
				zip_ref = zipfile.ZipFile(zip_file_name, 'r')
				zip_ref.extractall(model.get_folder())
				zip_ref.close() 
				model.log("Archive unpacked.")
					
			return redirect('/models/reload_model?model=' + str(model.id))
		
		return redirect('/model?model=' + str(model.id))
		
	model = ArtmModel.objects.get(id=request.GET['model_id'])
	if request.user != model.author:
		return HttpResponseForbidden("You are not the author.")
	context = {'model': model}
	return render(request, 'models/model_settings.html', Context(context))
