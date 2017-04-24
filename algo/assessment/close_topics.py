from models.models import ArtmModel, Topic 
import json
import numpy as np

#Number of assessment for each topic
ASSESS_RATIO = 5

def initialize_problem(problem):
	if problem.model:
		topics = dict()
		for topic in problem.model.get_topics(layer=problem.layer):
			topics[str(topic.index_id)] = 0
		N = len(topics)
		matrix = [[0 for j in range(N)] for i in range(N)]
		problem.params = json.dumps({"topics": topics, "matrix": matrix, "tasks_left": ASSESS_RATIO * N})
	else:
		problem.params = json.dumps({})
	problem.save()

def alter_problem(problem, request):
	print("ALTER PROBLEM")	
	POST = request.POST
	if POST["action"] == "change_model":
		if len(AssessmentTask.objects.filter(problem=problem)) > 0:
			raise ValueError("Cannot change model, because something already is assessed!")
		problem.model = ArtmModel.objects.get(id=POST["model_id"])
		topics = dict()
		for topic in  Topic.objects.filter(model=problem.model, layer=problem.model.layers_count):
			topics[str(topic.index_id)] = 0
		N = len(topics)
		matrix = [[0 for j in range(N)] for i in range(N)]
		problem.params = json.dumps({"topics" :topics, "matrix": matrix})
		#print(problem.params)
		problem.save()
	elif POST["action"] == "change_matrix":
		x = int(POST["x"])
		y = int(POST["y"])
		new_val = int(POST["new_val"])
		
		params = json.loads(problem.params)
		params["matrix"][x][y] = new_val
		problem.params = json.dumps(params)
		problem.save()
		
		
		
		
def get_problem_context(problem):
	params = json.loads(problem.params)
	ret =  {"problem": problem}
	if "matrix" in params:
		ret["topics"] = problem.model.get_topics()
		ret["matrix"] = params["matrix"]
	return ret
		
def get_task_context(task):
	ans = {}
	answer = json.loads(task.answer)
	ans["task"] = task
	ans["target_topic"] = Topic.objects.get(
		model=task.problem.model, 
		layer=task.problem.model.layers_count, 
		index_id=answer["target_topic_index_id"]
	)
	ans["topics"] = Topic.objects.filter(model=task.problem.model, layer=ans["target_topic"].layer).order_by("title")
	return ans
	
def create_task(problem, request):
	if not problem.model:
		raise ValueError("Model is not set.")

	from assessment.models import AssessmentTask
	
	params = json.loads(problem.params) 
	min_count = ASSESS_RATIO
	
	for key, value in params["topics"].items():
		if value < min_count:
			min_count = value
			min_topic = key
	
	if min_count == ASSESS_RATIO:
		return None
	else:
		params["topics"][min_topic] += 1
		params["tasks_left"] -= 1
		problem.params = json.dumps(params)		
		problem.save()
		task = AssessmentTask() 
		task.answer = json.dumps({"target_topic_index_id": min_topic})
		return task
	
 
	
def finalize_task(task, POST):
	params = json.loads(task.problem.params)
	answer = json.loads(task.answer)
	target_id = int(answer["target_topic_index_id"])
	# params["topics"][str(target_id)] += 1
	
	selected_topics = json.loads( POST["selected_topics"])
	
	for tid in selected_topics:
		params["matrix"][target_id][int(tid)] += 1
	
	task.problem.params = json.dumps(params)
	task.problem.save()
	 
	 
	answer["selected_topics"] = selected_topics
	task.answer = json.dumps(answer)
	task.save()
	
	
	
def get_problem_results(problem):
	params = json.loads(problem.params)
	ret = np.array(params["matrix"])
	N = ret.shape[0]
	for i in range(N):
		for j in range(N):
			ret[i][j] *= (1/params["topics"][str(i)])
	
	return ((1/(2*ASSESS_RATIO))*(ret + ret.transpose())).tolist()
	#from assessment.models import AssessmentTask
	#ans = []
	#for task in AssessmentTask.objects.filter(problem=problem):
	#	ans.append(json.loads(task.answer))	
	#return ans
	
def initialize_task(self):
	pass
	
def estimate_tasks(problem):
	return json.loads(problem.params)["tasks_left"]
		
		
	