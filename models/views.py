from django.shortcuts import render, redirect
from datasets.models import Dataset, Modality
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseNotFound
from models.models import ArtmModel, Topic, DocumentInTopic, TopTerm, TopicRelated, TopicInTopic
from django.contrib.auth.decorators import login_required, permission_required
import traceback
from django.conf import settings
import os


def visual_model(request):
	model = ArtmModel.objects.filter(id = request.GET['model'])[0]
	topics_count = model.topics_count.split()
	topics = Topic.objects.filter(model = model)
	topics_layers = [{"i": i + 1, "topics_count": topics_count[i+1], \
			"topics": topics.filter(layer = i + 1).order_by("spectrum_index")} for i in range (0, model.layers_count)]
	template = loader.get_template('models/model.html')
	context = Context({'model': model, 'topics_layers' : topics_layers})
	return render(request, 'models/model.html', context) 

@login_required
def reload_model(request):
	model = ArtmModel.objects.filter(id = request.GET['model'])[0]
	if "light" in request.GET:
		model.arrange_topics()
		#model.build_visualizations()
	else:
		model.reload()
	return HttpResponse("Reloaded. <a href ='/visual/model?model=" + str(model.id) + "'> Return to model</a>.") 

@login_required
def create_model(request):
	if request.method == 'GET': 
		try:
			target_dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
		except:
			return redirect("/")
		
		modalities = Modality.objects.filter(dataset = target_dataset)
		scripts = os.listdir(os.path.join(settings.DATA_DIR, "scripts"))
			 
		context = Context({'dataset': target_dataset,
						   'modalities': modalities,
						   'scripts': scripts})
		return render(request, 'models/create_model.html', context)
	
	dataset_name = request.POST['dataset']
	word_modality = request.POST['word_modality']
	model_name = request.POST['model_name']
	
	mode = request.POST['mode']
	
	try:
		dataset = Dataset.objects.filter(text_id = dataset_name)[0]
	except: 
		return HttpResponse("Dataset " + dataset_name + " does not exist.")
	print(request.POST)
	
	model = ArtmModel()
	model.dataset = dataset
	model.name = model_name
	model.main_modality = Modality.objects.filter(dataset = dataset, name = word_modality)[0]
	model.author = request.user
	model.save()
	
	#try:
	if mode == 'flat': 
		iter_count = int(request.POST.getlist('iter_count')[0])
		model.layers_count = 1
		model.topics_count = "1 " + request.POST.getlist('num_topics')[0]
		model.save()
		artm_object = model.create_simple(iter_count = iter_count)
	elif mode == "hier":
		model.layers_count = int(request.POST['num_layers'])
		iter_count = int(request.POST.getlist('iter_count')[1]) 
		model.topics_count = "1 " + ' '.join([request.POST.getlist('num_topics')[i + 1] for i in range(model.layers_count)])
		model.save()
		artm_object = model.create_simple(iter_count = iter_count)
	elif mode == "script":
		script_file_name = os.path.join(settings.DATA_DIR, "scripts", request.POST['script_name'])
		with open(script_file_name) as f:
			code = compile(f.read(), script_file_name, "exec")		
		batch_vectorizer, dictionary = dataset.get_batches()
		local_vars = {"batch_vectorizer": batch_vectorizer, "dictionary": dictionary}  
		print("Running custom sript...")		
		exec(code, local_vars)
		print("Custom script finished.")
		artm_object = local_vars["model"]
	elif mode == "custom":
		raise Exception("You cannot upload scripts.")
	else:
		raise Exception('Unknown mode.')
		
	model.save_matrices(artm_object)
	model.reload()
	return HttpResponse("Model created with " + str(model.layers_count) + " layers. <a href='/visual/model?model=" + str(model.id) + "'>View model.</a>")
	'''
	except:
		try:
			model.dispose()
		except:
			print("Error while disposing model.")
		ArtmModel.objects.filter(id = model.id).delete() 
		return HttpResponse("<p>Error:<br></p>" + "<p>" + traceback.format_exc() + "</p>")
	'''
	
	
@login_required
def delete_model(request):
	model = ArtmModel.objects.filter(id = request.GET['model'])[0]
	dataset_name = model.dataset.text_id 
	if 'sure' in request.GET and request.GET['sure'] == 'yes': 
		model.dispose()
		ArtmModel.objects.filter(id = request.GET['model']).delete()
		return HttpResponse("Model was deleted. <a href ='/visual/dataset?dataset=" + dataset_name + "'> Return to dataset</a>.")
	else:
		return HttpResponse("Are you sure that you want delete model " + str(model) + " permanently?<br>" + 
							"<a href = '/models/delete_model?model=" + str(model.id) + "&sure=yes'>Yes</a><br>" +
							"<a href = '/visual/dataset?dataset=" + dataset_name + "'>No</a>")
	

@login_required
def delete_all_models(request):
	dataset = Dataset.objects.filter(text_id = request.GET['dataset'])[0]
	models = ArtmModel.objects.filter(dataset = dataset)
	if 'sure' in request.GET and request.GET['sure'] == 'yes': 
		for model in models:
			model.dispose()
		models.delete()
		return HttpResponse("All models were deleted. <a href ='/visual/dataset?dataset=" + dataset.text_id + "'> Return to dataset</a>.")
	else:
		return HttpResponse("Are you sure that you want delete ALL models for dataset " + str(dataset) + " permanently?<br>" + 
							"<a href = '/models/delete_all_models?dataset=" + dataset.text_id + "&sure=yes'>Yes</a><br>" +
							"<a href = '/visual/dataset?dataset=" + dataset.text_id + "'>No</a>")	
							
def	visual_topic(request):
	try:
		target_topic = Topic.objects.filter(id = request.GET['id'])[0]
	except:
		return HttpResponseNotFound("<h1>Topic doesnt't exist</h1>")
	
	model = target_topic.model
	main_modality = target_topic.model.main_modality
	top_terms = TopTerm.objects.filter(topic = target_topic).order_by('-weight')
	top_terms = [term for term in top_terms if term.term.modality == main_modality]
	related_topics = TopicRelated.objects.filter(model = target_topic.model, topic1 = target_topic).order_by("weight")	
	context = {'model': target_topic.model, 'topic': target_topic, 'top_terms': top_terms, 'related_topics' : related_topics}
	
	if target_topic.layer == model.layers_count:
		documents = DocumentInTopic.objects.filter(topic = target_topic)
		#documents = documents[:100]
		context['documents'] = documents
		context['is_low'] = True
	else:
		topics = TopicInTopic.objects.filter(parent = target_topic)
		context['topics'] = topics
		context['is_low'] = False
		
	template = loader.get_template('models/topic.html')
	return HttpResponse(template.render(Context(context)))
	
def get_model_json(request):
	file_name = os.path.join(settings.DATA_DIR, "models", request.GET['model'], "hierarchy.json")
	with open(file_name) as file: 
		return HttpResponse(file.read(), content_type = 'application/json')  