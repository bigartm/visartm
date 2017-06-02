from models.models import ArtmModel, Topic 
from datasets.models import Document, Term


import os
import json
from django.db.models.functions import Lower
		
def initialize_problem(problem):
	problem.params = json.dumps({"order_mode" : "topic_first"})
	problem.save()
		
def get_problem_context(problem):
	params = json.loads(problem.params)
	ret = {"problem": problem, "params": params}
	ret["topics"] = Segmentation_Topic.objects.filter(problem=problem).order_by("id")
	return ret
	
def get_report_context(problem):
	from assessment.models import AssessmentTask, ProblemAssessor
	import numpy as np
	tasks = AssessmentTask.objects.filter(problem=problem)
	assessors = [x.assessor for x in ProblemAssessor.objects.filter(problem=problem)]
	
	N = max([x.id for x in assessors])+1
	current_tasks = np.zeros(N, dtype=int)
	skipped_tasks = np.zeros(N, dtype=int)
	done_tasks = np.zeros(N, dtype=int)
	words_count = np.zeros(N, dtype=int)
	segments_count = np.zeros(N, dtype=int)
	
	
	for task in tasks:
		if task.status == 1:
			current_tasks[task.assessor_id] += 1
		elif task.status == 2:
			if task.segments_selected > 0:
				done_tasks[task.assessor_id] += 1
			else:
				skipped_tasks[task.assessor_id]+=1
		words_count[task.assessor_id] += task.words_selected
		segments_count[task.assessor_id] += task.segments_selected
		
	ret = {}
	#ret["tasks"] = tasks 
	ret["assessors"] = [{
		"user":x, 
		"done_tasks": done_tasks[x.id], 
		"skipped_tasks": skipped_tasks[x.id],
		"current_tasks": current_tasks[x.id],
		"words_count": words_count[x.id],
		"segments_count": segments_count[x.id]
	} for x in assessors]
	
	return ret
	
def get_assessor_report(problem, request):
	from django.http import HttpResponse
	from django.contrib.auth.models import User
	from assessment.models import AssessmentTask
	assessor = User.objects.get(id=request.GET["assessor_id"])
	tasks = AssessmentTask.objects.filter(problem=problem, assessor=assessor)
	
	topics = {}
	for task in tasks:
		load_answer(task)
		text = task.document.get_text()
		for selection in task.answer["selections"]:
			sel_text = text[selection[0]: selection[1]]
			topic_id = selection[2]
			if not (topic_id in topics):
				topics[topic_id] = [sel_text]
			else:
				topics[topic_id].append(sel_text)
	
	if request.GET["type"] == "html":
		ans = ""
		for topic_id, selections in topics.items():
			ans += "<b>" + Segmentation_Topic.objects.get(problem=problem, index_id=topic_id).name + "</b><br>"
			ans += "<br>".join(selections)
			ans +="<br><br>"
		return HttpResponse(ans)
	elif request.GET["type"] == "xls":
		import pandas as pd
		from django.views.static import serve
		topics_list = []
		segments_list = []
		for topic_id, selections in topics.items():
			topic_name = Segmentation_Topic.objects.get(problem=problem, index_id=topic_id).name
			for x in selections:
				topics_list.append(topic_name)
				segments_list.append(x)
		
		df = pd.DataFrame({"Topic":topics_list, "Segment":segments_list})
		df = df[['Topic', 'Segment']]
		file_name = os.path.join(problem.get_folder(), "segments_%s.xlsx" % assessor.username)		
		writer = pd.ExcelWriter(file_name)
		df.to_excel(writer, assessor.username, index=False)
		writer.save()
 
		response = serve(request, os.path.basename(file_name), os.path.dirname(file_name))
		response['Content-Disposition'] = 'attachment; filename=segments_%s.xlsx' % assessor.username
		return response
		
def create_task(self, request):
	from assessment.models import AssessmentTask
	
	assessed_documents = set()
	for existing_task in AssessmentTask.objects.filter(problem=self):
		if existing_task.document:
			assessed_documents.add(existing_task.document.id)
	document_to_assess = None
	for document in Document.objects.filter(dataset=self.dataset):
		if not document.id in assessed_documents:
			document_to_assess = document
	if not document_to_assess:
		return  None
	task = AssessmentTask()
	task.document = document_to_assess
	return task
	
def alter_problem(self, request):
	POST = request.POST 
	params = json.loads(self.params) 
	if POST["action"] == "add_topic": 
		target = POST["name"]
		if len(target) > 2:
			topic = Segmentation_Topic()
			topic.problem = self
			
			try:
				topic.save()
			except:
				pass
			used_ids = set([topic.index_id for topic in Segmentation_Topic.objects.filter(problem=self)])
			topic.index_id = mex(used_ids)
		
			if target == "New topic":
				target = "New topic %d" % topic.index_id
			topic.name = target
			
			try:
				topic.save()
			except:
				pass 
				
	elif POST["action"] == "alter_topic":
		topic_id = POST["topic_id"]
		target = Segmentation_Topic.objects.get(id=topic_id)
		if "name" in POST:
			target.name = POST["name"]
		if "description" in POST:
			target.description = POST["description"]
		target.save()
		
	elif POST["action"] == "delete_topic":
		Segmentation_Topic.objects.filter(problem=self, index_id=POST["topic_id"]).delete()
		
	elif POST["action"] == "load_topics":
		try:
			topics_file = request.FILES['topics_file']
		except:
			return
		path = os.path.join(self.get_folder(), "topics.txt") 
		with open(path, 'wb+') as f:
			for chunk in topics_file.chunks():
				f.write(chunk) 
		with open(path, "r", encoding="utf-8") as f:
			input = json.loads(f.read())
		topics = input["topics"]
		Segmentation_Topic.objects.filter(problem=self).delete()
		for x in topics:
			topic = Segmentation_Topic()
			topic.name = x["name"]
			topic.description = x["description"]
			topic.index_id = x["id"]
			topic.problem=self
			topic.save()
	elif POST["action"] == "change_order_mode":
		print("CHANGE ORDER MODE")
		params["order_mode"] = POST["order_mode"]
	self.params = json.dumps(params)
	self.save()
	
	
def get_task_context(self):
	context = {"task": self}  	
	params = json.loads(self.problem.params)
	load_answer(self)
	if not "selections" in self.answer:
		self.answer["selections"] = []
	if not "topics_in" in self.answer:
		self.answer["topics_in"] = {}
	
	# Deal with topics
	
	all_topics = Segmentation_Topic.objects.filter(problem=self.problem).order_by(Lower("name"))
	topics_colors = {}
	for x, y in self.answer["topics_in"].items():
		topics_colors[int(x)] = y
		
	topics_send = [] 
	for topic in all_topics: 
		if topic.index_id in topics_colors:
			topics_send.append({"topic": topic, "color": topics_colors[topic.index_id]})
		else:
			topics_send.append({"topic": topic, "color": -1})
		
	context["topics"] = topics_send 	 
	
	# Get the text
	text = self.document.text
	
	
	word_index = self.document.get_word_index()
	term_beginnings = set()
	for x,_,_ in word_index:
		term_beginnings.add(x)
	
	
	
	# Find which terms are keywords (should be marekd as tags), they will be bold
	tags_ids = self.document.get_tags_ids()
	css = [0 for i in range(len(text))]			#1=keyword, 2=context
	if tags_ids:				
		for start_pos, length, term_index_id in word_index:
			if term_index_id in tags_ids:
				for i in range(start_pos, start_pos + length):
					css[i] = 1
	
	# find context
	line_start = 0
	is_context = True
	for i in range(len(text)+1):
		if i in term_beginnings:
			is_context = False
		if i == len(text) or text[i]=='\n':
			if is_context:
				for j in range(line_start, i):
					css[j] = 2
			is_context = True
			line_start = i
	  
	
	# Deal with text
	cur_pos = 0
	new_text = "<span offset='-20'>====================</span><br>"
	for sel in self.answer["selections"]:
		if sel[2] in topics_colors:
			new_text += text_to_span(text, cur_pos, sel[0], -1, css)
			new_text += text_to_span(text, sel[0], sel[1], topics_colors[sel[2]], css)
			cur_pos = sel[1] 
	new_text += text_to_span(text, cur_pos, len(text), -1, css)
	new_text += "<br><span offset=%d>====================</span>" % cur_pos
	context["text"] = new_text
	
	
	
	if "scroll_top" in self.answer:
		context["scroll_top"] = self.answer["scroll_top"]
	else:
		context["scroll_top"] = 0
	
	if 'selected_topic' in self.answer:
		context["selected_topic"] = self.answer["selected_topic"]
	else:
		context["selected_topic"] = -1
		
	context["topic_first"] =  (params["order_mode"] == "topic_first")
	return context
 
 
def alter_task(task, POST):
	load_answer(task)	
	if POST["action"] == "selection":
		new_selection_start = int(POST["selection_start"])
		new_selection_end = int(POST["selection_end"]) 
		
		if new_selection_start < 0:
			new_selection_start = 0
		doc_length = len(task.document.text)
		if new_selection_end > doc_length:
			new_selection_end = doc_length
		if new_selection_start >= new_selection_end:
			return 
		topic_id = int(POST["topic_id"])
		topic_use(task, topic_id)
		#if topic_id != -1:
		#	if not topic_id in answer["topics_in"]:
		#		answer["topics_in"].append(topic_id)
		
		if not "selections" in task.answer:
			task.answer["selections"] = []
		
		selections = [x for x in task.answer["selections"] if (x[0] >= new_selection_end or x[1] <= new_selection_start)]
		if topic_id != -1:
			selections.append([new_selection_start, new_selection_end, topic_id])
			
		# define selected terms and select such in that dataset, if they are not any other selection	
			
		selections.sort()
		task.answer["selections"] = selections
		task.answer["selected_topic"] = topic_id
	elif POST["action"] == "topic_use": 
		topic_use(task, POST["topic_id"])
	elif POST["action"] == "topic_not_use":
		topic_id = str(POST["topic_id"])
		if "topics_in" in task.answer and topic_id in task.answer["topics_in"]:
			del task.answer["topics_in"][topic_id]
	
	if "scroll_top" in POST:
		task.answer["scroll_top"] = POST["scroll_top"]

	save_answer(task) 
	
def topic_use(task, topic_id): 
	if not str(topic_id) in task.answer["topics_in"]:
		print("NEWW")
		used_colors = set([color for _, color in task.answer["topics_in"].items()])
		task.answer["topics_in"][str(topic_id)] = mex(used_colors) 
		task.answer["selected_topic"] = topic_id
	else:
		print("ALREADY IS")
		
def initialize_task(task):
	load_answer(task)	
	if not 'selections' in task.answer:
		task.answer["selections"] = []
	if not 'topics_in' in task.answer:
		task.answer["topics_in"] = {}
	word_index = task.document.get_word_index()
	text_terms = [x[2] for x in word_index]
	
	cur_term = 0
	while cur_term < len(text_terms): 
		segment = None
		length = 0
		candidates = Segmentation_TypicalSegment.objects.filter(problem=task.problem, first_term_id=text_terms[cur_term]).order_by("-length")
		for candidate in candidates:
			candidate_terms = json.loads(candidate.terms)
			length = len(candidate_terms)
			if candidate_terms == text_terms[cur_term : cur_term + length]:
				segment = candidate
				break
		if segment:
			topic_id = candidate.get_best_topic()
			if not topic_id in task.answer["topics_in"]:
				save_answer(task)
				task.alter({"action": "topic_use", "topic_id": str(topic_id)})
			end_pos = word_index[cur_term + length - 1][0] + word_index[cur_term + length - 1][1] 
			task.answer["selections"].append([word_index[cur_term][0], end_pos, topic_id])
			cur_term += length
		else:
			cur_term += 1 
	save_answer(task)

def finalize_task(task, POST):
	load_answer(task) 
	selections = task.answer["selections"]
	word_index = task.document.get_word_index()
	terms_assessions = [-1 for i in range(len(word_index))]
	assessed_segments = []
	for selection_start, selection_end, topic_id in selections:
		terms = []
		i = 0
		for term_start, term_length, term_id in word_index:
			if term_start >= selection_start and term_start + term_length <= selection_end:
				terms.append(term_id)
				terms_assessions[i] = topic_id
			i += 1
			
		if len(terms) > 1:
			assessed_segments.append([terms, topic_id])
			segment = Segmentation_TypicalSegment.get_segment(task.problem, terms)
			segment.add_topic(topic_id)
	
		task.words_selected += len(terms)
		
	
	task.answer["terms_assessions"] = terms_assessions
	task.answer["assessed_segments"] = assessed_segments
	task.segments_selected = len(selections)
	save_answer(task)
	
def get_problem_results(problem):
	from assessment.models import AssessmentTask
	params = json.loads(problem.params) 
	results = dict()
	term_index = Term.objects.filter(dataset=problem.dataset).order_by("index_id")
	term_index = [t.text for t in term_index]
	result_topics = []
	
	for topic in Segmentation_Topic.objects.filter(problem=problem):
		result_topics.append({"id":topic.index_id, "name": topic.name, "description": topic.description})			
		
	results["topics"] = result_topics
	results["documents"] = []
	for task in AssessmentTask.objects.filter(problem=problem):
		if task.status == 2:
			load_answer(task)
			terms_assessions = task.answer["terms_assessions"]
			word_index = task.document.get_word_index()
			#print("Building words")
			words = [term_index[w[2]] for w in word_index]
			terms = ""
			#print("L:: %d" % len(word_index))
			for i in range(len(words)):
				terms += ("%s:%d " % (words[i], terms_assessions[i]))
				
			results["documents"].append({
				"title" : task.document.title,
				"terms" : terms, 
				"selections" : task.answer["selections"]
			})
	return results
	
def estimate_tasks(problem):
	from assessment.models import AssessmentTask
	done = len(AssessmentTask.objects.filter(problem=problem, status=2))
	current = len(AssessmentTask.objects.filter(problem=problem, status=1))
	return problem.dataset.documents_count - ret["done"] - ret["current"]
		
# Loads answer data for task (from file at certain location) and stores	it to task.answer
def load_answer(task):
	path = os.path.join(task.problem.get_folder(), task.document.text_id)
	try: 
		with open(path, "r") as f:
			text = f.read()
		task.answer = json.loads(text)
	except:
		task.answer =  {} 
	
def save_answer(task): 
	path = os.path.join(task.problem.get_folder(), task.document.text_id)
	with open(path, "w") as f:
		f.write(json.dumps(task.answer))

### Specific models for segmentation assessment
from django.db import models 

class Segmentation_Topic(models.Model):
	problem = models.ForeignKey("AssessmentProblem", null=False)
	name = models.TextField(null=False, default="New topic")
	description = models.TextField(null=False, default="Description")
	index_id = models.IntegerField(null=False, default = 0)
		
	def description_html(self):
		return '<br>'.join(self.description_lines())
	
	def description_lines(self):
		return [line.strip() for line in self.description.split("\n")] 
	
	class Meta:
		unique_together = (("problem", "name"),("problem", "index_id"))
		app_label="assessment"
		
class Segmentation_TypicalSegment(models.Model):
	problem = models.ForeignKey("AssessmentProblem", null=False, default=0)
	first_term_id = models.IntegerField(null=False, default=0)
	terms = models.TextField(null=False, default="")
	topics = models.TextField(null=False, default="")
	length = models.IntegerField(null=False, default=1)
	
	class Meta:
		app_label="assessment"
		
	def get_segment(problem, terms):
		key = json.dumps(terms)
		candidates = Segmentation_TypicalSegment.objects.filter(problem=problem, first_term_id=terms[0])
		candidates = candidates.filter(terms=key)
		if len(candidates) > 0:
			return candidates[0]
		else:
			segment = Segmentation_TypicalSegment()
			segment.problem = problem
			segment.first_term_id = terms[0]
			segment.terms = key
			segment.topics = "{}"
			segment.length = len(terms)
			segment.save()
			return segment
			
			
			
	def add_topic(self, topic_id):
		topic_id = str(topic_id)
		topics = json.loads(self.topics)
		if not topic_id in topics:
			topics[topic_id] = 1
		else:
			topics[topic_id] += 1
		self.topics = json.dumps(topics)
		self.save()
	
	def get_best_topic(self):
		topics = json.loads(self.topics)
		return int(max(topics, key=topics.get))
		
		
		
			
def get_css(class_id, css_id):
	if css_id == 2:
		return "context"
	ret = ""
	if css_id == 1:
		ret += "keyword "
	if class_id > 0:
		ret += "tpc" + str(class_id)
	return ret
	
# TODO: to separate file
def text_to_span(text, start, end, class_id, css):
	if start >= end:
		return ""
	cur_css = css[start]
	ret = "<span class='%s' offset=%d>" % (get_css(class_id, cur_css), start)
	for pos in range(start, end):
		if text[pos]=='\n':
			ret += "</span><br><span class='%s' offset=%d>" % (get_css(class_id, cur_css),  pos + 1)
		else:
			if pos != start and css[pos] != cur_css:
				cur_css = css[pos]
				ret += "</span><span class='%s' offset=%d>" % (get_css(class_id, cur_css), pos)
			ret += text[pos]
	return ret + "</span>"
		 
		 
def mex(values):
	for i in range(1,1000000):
		if not i in values:
			return i
		

	