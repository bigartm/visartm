from django.shortcuts import render, redirect
from django.template import Context
from threading import Thread
from django.conf import settings
import os

from datasets.models import Dataset
from models.models import ArtmModel
from visual.models import GlobalVisualization
import visartm.views as general_views

def visual_global(request):
	model = ArtmModel.objects.get(id = request.GET['model'])
	dataset = model.dataset 
		
	visual_name = request.GET['type']
	
	if model == None:
		return general_views.message(request, "You have to create model first.<br>" + \
							"<a href='/models/create?dataset=" + dataset.text_id + "'>Create model</a><br>"     + \
							"<a href='/dataset?dataset=" + dataset.text_id + "'>Return to dataset</a><br>")

							
	if 'try' in request.GET and request.GET['try'] == 'again':
		GlobalVisualization.objects.filter(model = model, name = visual_name).delete()
		return redirect("/visual/global?type=" + visual_name + "&model=" + str(model.id))
		
		
	try:
		visualization = GlobalVisualization.objects.filter(model = model, name = visual_name)[0]			
	except:
		visualization = GlobalVisualization()
		visualization.name = visual_name
		visualization.model = model
		visualization.status = 0
		visualization.save()
		
		if settings.THREADING:
			t = Thread(target = GlobalVisualization.render_untrusted, args = (visualization,), daemon = True)
			t.start()
		else:
			#print("RENDER")
			visualization.render()
			
	if visualization.status == 0:
		return general_views.wait(request, "Pending...", visualization.start_time, period = "2") 
	elif visualization.status == 2:
		return general_views.message(request, "Error during rendering.<br>" + visualization.error_message.replace('\n', "<br>") +   \
				"<br><br><a href='/visual/global?type=" + visual_name + \
				"&model=" + str(model.id) + "&try=again'>Try again</a>")
	
	
	data_file_name = os.path.join(model.get_visual_folder(), visual_name + ".txt")
	with open(data_file_name, "r", encoding = 'utf-8') as f:
		data = f.read()
	context = Context({'dataset': dataset,
	                   'model': model,
						'data': data,
						'no_footer': True})				   
	return render(request, "visual/" + visual_name.split('_')[0] + ".html", context)
 