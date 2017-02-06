from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse
from django.template import Context
import os
from threading import Thread
from datetime import datetime

from research.models import Research
from datasets.models import Dataset
from models.models import ArtmModel
from assessment.models import AssessmentProblem
import visartm.views as general_views


def create_research(request):
	if request.method == 'POST':
		print(request.POST) 
		research = Research()
		research.dataset = Dataset.objects.get(id=request.POST['dataset_id'])
		try:
			research.model = ArtmModel.objects.get(id=request.POST['model_id'])
		except:
			pass
		try:
			research.problem = AssessmentProblem.objects.get(id=request.POST['problem_id'])
		except:
			pass
		research.script_name = request.POST['script_name']
		research.researcher = request.user
		research.status = 1 
		research.save()
		
		if settings.THREADING:
			t = Thread(target = Research.run, args = (research,), daemon = True)
			t.start()
		else:
			research.run()
			 
		return redirect("/research/" + str(research.id) + "/")
		
	dataset = Dataset.objects.get(id=request.GET["dataset_id"])
	models = ArtmModel.objects.filter(dataset=dataset)
	problems = AssessmentProblem.objects.filter(dataset=dataset)
	script_names = os.listdir(os.path.join(settings.BASE_DIR, "algo", "research"))
		
	context = Context({"dataset":dataset, "models":models, "problems":problems, "script_names":script_names})
	return render(request, "research/create_research.html", context) 
	
def rerun_research(request):
	research = Research.objects.get(id=request.GET['id'])
	if research.researcher != request.user:
		return HttpResponseForbidden("You are not authorized to rerun this report.")
	research.start_time = datetime.now()
	research.status = 1 
	research.save()		
	
	if settings.THREADING:
		t = Thread(target = Research.run, args = (research,), daemon = True)
		t.start()
	else:
		research.run()
	return redirect("/research/" + str(research.id) + "/")
	
	
def show_research(request, research_id):
	research = Research.objects.get(id=research_id)
	if research.researcher != request.user:
		return HttpResponseForbidden("You are not authorized to see this report.")
	
	if research.status == 3:
		return general_views.message(request, "Error during rendering.<br>" + research.error_message.replace('\n', "<br>"))
		
	with open(research.get_report_file(), "r") as f:
		response = HttpResponse(f.read(), content_type='text/html')
	
	if research.status == 1:
		response['Refresh'] = "10"
	return response
	
def get_picture(request, research_id, pic_id):
	path = os.path.join(settings.BASE_DIR, "data", "research", research_id, "pic", pic_id + ".png")
	with open(path, "rb") as f:
		return HttpResponse(f.read(), content_type="image/png")
		
		
		
		