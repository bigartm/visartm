import os
import json

from models.models import ArtmModel, Topic 
from datasets.models import Document, Term

		
def initialize_problem(problem):
	problem.params = json.dumps({})
	problem.save()
		
def get_problem_context(problem):
	params = json.loads(problem.params)
	context = {"problem": problem, "params": params}
	return context
	
def create_task(problem, request):
	from assessment.models import AssessmentTask
	return None
	
def alter_problem(problem, request):
	params = json.loads(problem.params) 
	if request.POST["action"] == "some_action":
		pass
	problem.params = json.dumps(params)
	problem.save()
	
def get_task_context(task):
	context = {"task": task} 
	return context
 
def alter_task(task, POST):
	if POST["action"] == "some_action":
		pass
	
def initialize_task(task):
	pass

def finalize_task(task, POST):
	pass
	
def get_problem_results(problem): 
	from assessment.models import AssessmentTask
	results = {}
	return results

	