from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.template import Context
from django.contrib.auth.decorators import login_required
from datetime import datetime

from datasets.models import Dataset
from assessment.models import AssessmentProblem, AssessmentTask, ProblemAssessor
from django.contrib.auth.models import User	
import visartm.views as general_views
	
@login_required	
def problem(request):
	if request.method == 'POST':
		problem = AssessmentProblem.objects.get(id = request.POST["problem_id"]) 
		problem.alter(request.POST)
		return redirect("/assessment/problem?problem_id=" + str(problem.id))
	
	if "problem_id" in request.GET:
		problem = AssessmentProblem.objects.get(id = request.GET["problem_id"])
		problem.refresh()
		if problem.dataset.owner != request.user:
			return HttpResponseForbidden("Only owner of dataset (" + str(problem.dataset.owner) + ") can see assessment problem.")
		return render(request, "assessment/superviser/" + problem.type + ".html", Context(problem.get_view_context()))
	else:
		dataset_id = int(request.GET["dataset_id"])
		type = request.GET["type"]
		try:
			problem = AssessmentProblem.objects.get(dataset_id=dataset_id, type=type)
		except:
			dataset = Dataset.objects.get(id = dataset_id)		
			if dataset.owner != request.user:
				return HttpResponseForbidden("Only owner of dataset (" + str(problem.dataset.owner) + ") can create assessment problem.")
			problem = AssessmentProblem()
			problem.dataset = dataset
			problem.type = type
			problem.save()
			
			relation = ProblemAssessor()
			relation.problem = problem
			relation.assessor = request.user
			relation.save()
			
		return redirect("/assessment/problem?problem_id=" + str(problem.id))
	

@login_required
def get_task(request):
	problem = AssessmentProblem.objects.get(id = request.GET["problem_id"])	
	problem.refresh()
		
	if len(ProblemAssessor.objects.filter(problem=problem, assessor=request.user))!=0:
		task = problem.create_task()
		if not task:
			return general_views.message(request, "Seems like everything is assessed!")
		return redirect("/assessment/task?task_id=" + str(task.id))
	else:
		return HttpResponseForbidden("You are not allowed to make assessions in this task.")
	
@login_required
def task(request):
	if request.method == 'POST':
		task = AssessmentTask.objects.get(id = request.POST["task_id"])
		return general_views.message(request, "Thank you! Assess one more task?<br>" + \
							"<a href='/assessment/get_task?problem_id=" + str(task.problem.id) + "'>Yes</a>.<br>"     + \
							"<a href='/dataset?dataset=" + task.problem.dataset.text_id + "'>No</a>.<br>")
	
	task = AssessmentTask.objects.get(id = request.GET["task_id"])
	if task.assessor != request.user:
		return HttpResponseForbidden("This is not your task.")
	return render(request, "assessment/assessor/" + self.problem.type + ".html", Context(task.get_view_context()))
	
	
def add_assessor(request):
	problem = AssessmentProblem.objects.get(id=request.GET["problem_id"])
	if request.user != problem.dataset.owner:
		return HttpResponseForbidden("You are not owner.")
	relation = ProblemAssessor()
	relation.assessor = User.objects.get(username = request.GET["username"])
	relation.problem = problem
	relation.save()
	return redirect("/dataset?dataset=" + problem.dataset.text_id + "&mode=assessment")
	
def delete_assessor(request):	
	problem = AssessmentProblem.objects.get(id=request.GET["problem_id"])
	if request.user != problem.dataset.owner:
		return HttpResponseForbidden("You are not owner.")
	ProblemAssessor.objects.filter(problem = problem, assessor__username = request.GET["username"]).delete()
	return redirect("/dataset?dataset=" + problem.dataset.text_id + "&mode=assessment")
			
		
		
	
	
