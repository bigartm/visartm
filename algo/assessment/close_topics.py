from models.models import ArtmModel, Topic 

import json


def initialize_problem(problem):
	problem.params = json.dumps({})
	problem.save()

def alter_problem(problem, request):
	from assessment.models import AssessmentTask
	if request.POST["action"] == "change_model":
		if len(AssessmentTask.objects.filter(problem=problem)) > 0:
			raise ValueError("Cannot change model, because something already is assessed!")
		problem.model = ArtmModel.objects.get(id=request.POST["model_id"])
		topics = dict()
		for topic in  Topic.objects.filter(model=problem.model, layer=problem.model.layers_count):
			topics[str(topic.id)] = 0
		problem.params = json.dumps({"topics" :topics})
		print(problem.params)
		problem.save()
		
def get_problem_context(problem):
	return {"problem": problem, "models": ArtmModel.objects.filter(dataset=problem.dataset)}
		
def get_task_context(task):
	ans = {}
	answer = json.loads(task.answer)
	ans["task"] = task
	ans["target_topic"] = Topic.objects.get(id=answer["target_topic_id"])
	ans["topics"] = Topic.objects.filter(model=task.problem.model, layer=ans["target_topic"].layer).order_by("title")
	return ans
	
def create_task(problem, request):
	from assessment.models import AssessmentTask
	
	params = json.loads(problem.params)
	#print (params)
	for key, value in params["topics"].items():
		if value == 0:
			task = AssessmentTask() 
			task.answer = json.dumps({"target_topic_id": key})
			task.problem = problem
			task.assessor = request.user
			task.save()
			return task
	return None
	
 
	
def finalize_task(task, POST):
	params = json.loads(task.problem.params)
	answer = json.loads(task.answer)
	params["topics"][answer["target_topic_id"]] += 1
	
	task.problem.params = json.dumps(params)
	task.problem.save()
	 
	answer["selected_topics"] = json.loads( POST["selected_topics"])
	task.answer = json.dumps(answer)
	task.save()
	
	
	
def get_problem_results(problem):
	from assessment.models import AssessmentTask
	ans = []
	for task in AssessmentTask.objects.filter(problem=problem):
		ans.append(json.loads(task.answer))
		
	return ans
	
def initialize_task(self):
	pass
	
def count_tasks(problem):
	from assessment.models import AssessmentTask
	ret = dict()
	ret["done"] = len(AssessmentTask.objects.filter(problem=problem, status=2))
	ret["current"] = len(AssessmentTask.objects.filter(problem=problem, status=1))
	ret["estimate"] = "Unknown" 
	return ret
	