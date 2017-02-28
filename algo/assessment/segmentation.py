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
	self.load_answer()
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
 
 
def alter_task(self, POST):
	self.load_answer()	
	if POST["action"] == "selection":
		new_selection_start = int(POST["selection_start"])
		new_selection_end = int(POST["selection_end"]) 
		
		if new_selection_start < 0:
			new_selection_start = 0
		doc_length = len(self.document.text)
		if new_selection_end > doc_length:
			new_selection_end = doc_length
		if new_selection_start >= new_selection_end:
			return 
		topic_id = int(POST["topic_id"])
		#if topic_id != -1:
		#	if not topic_id in answer["topics_in"]:
		#		answer["topics_in"].append(topic_id)
		
		if not "selections" in self.answer:
			self.answer["selections"] = []
		
		selections = [x for x in self.answer["selections"] if (x[0] >= new_selection_end or x[1] <= new_selection_start)]
		if topic_id != -1:
			selections.append([new_selection_start, new_selection_end, topic_id])
			
		# define selected terms and select such in that dataset, if they are not any other selection	
			
		selections.sort()
		self.answer["selections"] = selections
		self.answer["selected_topic"] = topic_id
	elif POST["action"] == "topic_use": 
		topic_id = int(POST["topic_id"]) 
		if not "topics_in" in self.answer:
			self.answer["topics_in"] = {}
		if not topic_id in self.answer["topics_in"]:
			used_colors = set([color for _, color in self.answer["topics_in"].items()])
			self.answer["topics_in"][topic_id] = mex(used_colors) 
			self.answer["selected_topic"] = topic_id
	elif POST["action"] == "topic_not_use":
		topic_id = str(POST["topic_id"])
		if "topics_in" in self.answer and topic_id in self.answer["topics_in"]:
			del self.answer["topics_in"][topic_id]
	
	if "scroll_top" in POST:
		self.answer["scroll_top"] = POST["scroll_top"]

	self.save_answer() 
	
	
def initialize_task(self):
	self.load_answer()	
	if not 'selections' in self.answer:
		self.answer["selections"] = []
	if not 'topics_in' in self.answer:
		self.answer["topics_in"] = {}
	word_index = self.document.get_word_index()
	text_terms = [x[2] for x in word_index]
	
	cur_term = 0
	while cur_term < len(text_terms): 
		segment = None
		length = 0
		candidates = Segmentation_TypicalSegment.objects.filter(problem=self.problem, first_term_id=text_terms[cur_term]).order_by("-length")
		for candidate in candidates:
			candidate_terms = json.loads(candidate.terms)
			length = len(candidate_terms)
			if candidate_terms == text_terms[cur_term : cur_term + length]:
				segment = candidate
				break
		if segment:
			topic_id = candidate.get_best_topic()
			if not topic_id in self.answer["topics_in"]:
				self.save_answer()
				self.alter({"action": "topic_use", "topic_id": str(topic_id)})
			end_pos = word_index[cur_term + length - 1][0] + word_index[cur_term + length - 1][1] 
			self.answer["selections"].append([word_index[cur_term][0], end_pos, topic_id])
			cur_term += length
		else:
			cur_term += 1 
	self.save_answer()

def finalize_task(self, POST):
	self.load_answer() 
	selections = self.answer["selections"]
	word_index = self.document.get_word_index()
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
			segment = Segmentation_TypicalSegment.get_segment(self.problem, terms)
			segment.add_topic(topic_id)
			
	self.answer["terms_assessions"] = terms_assessions
	self.answer["assessed_segments"] = assessed_segments 
	self.save_answer()
	
def get_problem_results(self):
	from assessment.models import AssessmentTask
	params = json.loads(self.params) 
	results = dict()
	term_index = Term.objects.filter(dataset=self.dataset).order_by("index_id")
	result_topics = []
	
	for topic in Segmentation_Topic.objects.filter(problem=self):
		result_topics.append({"id":topic.index_id, "name": topic.name, "description": topic.description})			
		
	results["topics"] = result_topics
	results["documents"] = []
	for task in AssessmentTask.objects.filter(problem=self):
		if task.status == 2:
			task.load_answer()
			terms_assessions = task.answer["terms_assessions"]
			word_index = task.document.get_word_index()
			terms = ""
			for i in range(len(word_index)):
				terms += term_index[word_index[i][2]].text + ":" + str(terms_assessions[i]) + " "
			results["documents"].append({
				"title" : task.document.title,
				"terms" : terms 
			})
	return results
	
def count_tasks(problem):
	from assessment.models import AssessmentTask
	ret = dict()
	ret["done"] = len(AssessmentTask.objects.filter(problem=problem, status=2))
	ret["current"] = len(AssessmentTask.objects.filter(problem=problem, status=1))
	ret["estimate"] = problem.dataset.documents_count - ret["done"] - ret["current"] 
	return ret
		
	
### Specific models for segmentation assessment
from django.db import models 

class Segmentation_Topic(models.Model):
	problem = models.ForeignKey("AssessmentProblem", null=False)
	name = models.TextField(null=False, default="New topic")
	description = models.TextField(null=False, default="Description")
	index_id = models.IntegerField(null=False, default = 0)
		
	def description_html(self):
		return self.description.replace("\n","<br>")
	
	def description_lines(self):
		return [line[:-1] for line in self.description.split("\n")] 
	
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
		

	