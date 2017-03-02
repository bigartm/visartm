import os
import json
import random

from models.models import ArtmModel, Topic 
from datasets.models import Document, Term

ASSESS_RATIO = 3
ASSESS_LENGTH = 6
		
def initialize_problem(problem):
	if problem.model:
		N = len(problem.model.get_topics(layer=problem.layer))
		problem.params = json.dumps({"topics_count": N, "tasks_left": N * ASSESS_RATIO})
		problem.save()
			
def get_problem_context(problem):
	params = json.loads(problem.params)
	context = {"problem": problem, "params": params}
	return context
	
def create_task(problem, request):
	from assessment.models import AssessmentTask
	params = json.loads(problem.params) 
	N = params["topics_count"] 
		
	if params["tasks_left"] == 0:
		return None
	else:
		params["tasks_left"] -= 1
		problem.params = json.dumps(params)	
		problem.save()
		task = AssessmentTask() 
		topics = random.sample(range(N), min(ASSESS_LENGTH, N))
		task.answer = json.dumps({"topics": topics})
		return task
	
def alter_problem(problem, request):
	pass
	
def get_task_context(task):
	context = {"task": task, "topics": []} 
	topics = task.problem.model.get_topics(layer=task.problem.layer)
	for topic_index_id in json.loads(task.answer)["topics"]:
		context["topics"].append(topics.get(index_id=topic_index_id))
	return context
 
def alter_task(task, POST):
	answer = json.loads(task.answer)
	topic_id = int(POST["topic_index_id"])
	pos = -1
	N = len(answer["topics"])
	for i in range(N):
		if answer["topics"][i] == topic_id:
			pos = i
			break
	if pos == -1:
		return
		
	if POST["action"] == "topic_up":
		if pos == 0:
			return
		answer["topics"][pos-1], answer["topics"][pos] = answer["topics"][pos], answer["topics"][pos-1]
	elif POST["action"] == "topic_down":
		if pos == N-1:
			return
		answer["topics"][pos+1], answer["topics"][pos] = answer["topics"][pos], answer["topics"][pos+1]
	task.answer = json.dumps(answer)
	task.save()
	
def initialize_task(task):
	pass

def finalize_task(task, POST):
	pass
	
def get_problem_results(problem): 
	from assessment.models import AssessmentTask
	results = []
	for task in AssessmentTask.objects.filter(problem=problem):
		results.append(json.loads(task.answer)["topics"])	
	return results
	
def estimate_tasks(problem):
	return json.loads(problem.params)["tasks_left"]

	