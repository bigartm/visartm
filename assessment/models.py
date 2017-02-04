from django.db import models 
from datasets.models import Dataset, Document, Term
from django.contrib.auth.models import User	
from datetime import datetime, timedelta
import json

class AssessmentProblem(models.Model):
	type = models.TextField() 
	dataset = models.ForeignKey(Dataset)
	params = models.TextField(null=False, default = "{}")
	last_refreshed = models.DateTimeField(null=False, default=datetime.now) 
	timeout = models.IntegerField(null=False, default=3600)
	
	def __str__(self):
		return self.dataset.name + "/" + self.type

	# Get superviser/instructions view. Returns view context as dict.
	def get_view_context(self):
		ret = {"problem": self, "params": json.loads(self.params)}
		if self.type == "segmentation":
			ret["topics"] = Segmentation_Topic.objects.filter(problem=self).order_by("id")
		return ret
	
	# Create Task instance, initialize it and save it	
	def create_task(self, request):
		self.refresh()
		task = AssessmentTask()
		if self.type == "segmentation":
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
			task.document = document_to_assess
			
		task.problem = self
		task.status = 1
		task.assessor = request.user
		task.initialize()
		task.save()
		return task
	
	def initialize(self):
		if self.type == "segmentation":
			pass
		self.save()
		
	# Allows superviser or assessor alter some global parameters of assessment problem
	def alter(self, POST):
		print("ALTER PROBLEM", POST)
		params = json.loads(self.params) 
		if self.type == "segmentation":
			if not "topics" in params:
					params["topics"] = []
				
			if POST["action"] == "add_topic":
				print("ADD TOPIC")
				target = POST["name"]
				if len(target) > 2:
					topic = Segmentation_Topic()
					topic.problem = self
					topic.name = target
					topic.save()
			
			elif POST["action"] == "alter_topic":
				topic_id = POST["topic_id"]
				target = Segmentation_Topic.objects.get(id=topic_id)
				if "name" in POST:
					target.name = POST["name"]
				if "description" in POST:
					target.description = POST["description"]
				target.save()
				
			elif POST["action"] == "delete_topic":
				Segmentation_Topic.objects.filter(id=POST["topic_id"]).delete()
			
		self.params = json.dumps(params)
		self.save()
	
	# Return number of completed and current task. Estimates how many tasks are to be done
	def count_tasks(self):
		ret = dict()
		ret["done"] = len(AssessmentTask.objects.filter(problem=self, status=2))
		ret["current"] = len(AssessmentTask.objects.filter(problem=self, status=1))
		ret["estimate"] = "Unknown"
		if self.type == "segmentation":
			ret["estimate"] = self.dataset.documents_count - ret["done"] - ret["current"] 
		return ret
	
	# Return results as object
	def get_results(self):
		params = json.loads(self.params) 
		results = dict()
		
		if self.type == "segmentation":
			results["topics"] = params["topics"]
			results["documents"] = []
			for task in AssessmentTask.objects.filter(problem=self):
				if task.status == 2:
					answer = json.loads(task.answer) 
					results["documents"].append({
						"title" : task.document.title,
						"answer" : answer 
					})
		return results
    
	
	# Delete all 'dead' tasks
	def refresh(self):
		now = datetime.now()
		if (now - self.last_refreshed).seconds < 150:
			return
		print("Will refresh")
		deadline = now - timedelta(0, self.timeout)
		dead_tasks = AssessmentTask.objects.filter(problem=self, status=1, creation_time__lte=deadline)
		#for task in dead_tasks:
		#	task.status = 3
		#	task.save()
		dead_tasks.delete()
		self.last_refreshed = now
		self.save()
			
	
# TODO: to separate file
def text_to_span(text, start, end, class_id, bold_chars=set()): 
	ret = "<span class='tpc%d' offset=%d>" % ( class_id, start)
	for pos in range(start, end):
		if text[pos]=='\n':
			ret += "</span><br><span class='tpc%d' offset=%d>" % (class_id, pos + 1)
		else:
			if pos in bold_chars:
				ret += "<b>" + text[pos] + "</b>"
			else:
				ret += text[pos]
	return ret + "</span>"
		
class AssessmentTask(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False)
	assessor = models.ForeignKey(User, null=False, default=0)
	document = models.ForeignKey(Document, null = True)
	question = models.TextField(null = True)
	answer = models.TextField(null=False, default="{}")
	creation_time = models.DateTimeField(null=False, default = datetime.now) 
	completion_time = models.DateTimeField(null=True)
	status = models.IntegerField(null=False, default = 0)  # 1-issued, 2-completed
	
	# Get assessor view. Returns view context as dict.
	def get_view_context(self):
		context = {"task": self}  	
		params = json.loads(self.problem.params)
		answer = json.loads(self.answer)
		
		if self.problem.type == "segmentation":
			if not "selections" in answer:
				answer["selections"] = []
			if not "topics_in" in answer:
				answer["topics_in"] = []
			
			# Deal with topics
			all_topics = Segmentation_Topic.objects.filter(problem=self.problem)
			topics_in = answer["topics_in"]
			context["topics_in"] = [topic for topic in all_topics if topic.id in topics_in]
			context["topics_out"] = [topic for topic in all_topics if not topic.id in topics_in]			
			context["topics_count"] = len(context["topics_in"])
			topics_class_ids = dict()
			i = 0
			for topic in context["topics_in"]:
				i += 1
				topics_class_ids[topic.id] = i
			
			# Find which terms are keywords (should be marekd as tags), they will be bold
			tags_ids = self.document.get_tags_ids()
			bold_chars = set()
			if tags_ids:
				word_index = self.document.get_word_index()
				for start_pos, length, term_index_id in word_index:
					if term_index_id in tags_ids:
						for i in range(start_pos, start_pos + length):
							bold_chars.add(i)
				
			# Deal with text
			text = self.document.text
			cur_pos = 0
			new_text = "<span offset='-20'>====================</span><br>"
			for sel in answer["selections"]:
				if sel[2] in topics_class_ids:
					new_text += text_to_span(text, cur_pos, sel[0], -1, bold_chars=bold_chars)
					new_text += text_to_span(text, sel[0], sel[1], topics_class_ids[sel[2]], bold_chars=bold_chars)
					cur_pos = sel[1] 
			new_text += text_to_span(text, cur_pos, len(text), -1, bold_chars=bold_chars)
			new_text += "<br><span offset=%d>====================</span>" % cur_pos
			context["text"] = new_text
			
			
			
			if "scroll_top" in answer:
				context["scroll_top"] = answer["scroll_top"]
			else:
				context["scroll_top"] = 0
			
			
		return context
		
	def initialize(self):
		answer = dict()
		if self.problem.type == "segmentation":
			selections = []
			topics_in = []
			word_index = self.document.get_word_index()
			text_terms = [x[2] for x in word_index]
			
			cur_term = 0
			while cur_term < len(text_terms): 
				segment = None
				length = 0
				candidates = Segmentation_TypicalSegment.objects.filter(problem=self.problem, first_term_id=text_terms[cur_term])
				for candidate in candidates:
					candidate_terms = json.loads(candidate.terms)
					length = len(candidate_terms)
					if candidate_terms == text_terms[cur_term : cur_term + length]:
						segment = candidate
						break
				if segment:
					topic_id = candidate.get_best_topic()
					if not topic_id in topics_in:
						topics_in.append(topic_id)
					end_pos = word_index[cur_term + length - 1][0] + word_index[cur_term + length - 1][1] 
					selections.append([word_index[cur_term][0], end_pos, topic_id])
					cur_term += length
				else:
					cur_term += 1
					
			answer["selections"] = selections
			answer["topics_in"] = topics_in
			
		self.answer = json.dumps(answer)
		self.save()
		
	def alter(self, POST):
		answer = json.loads(self.answer) 
		answer["last_post_request"] = POST
		print("ALTER TASK", POST)
		
		if self.problem.type == "segmentation":
			if not "selections" in answer:
				answer["selections"] = []
			if not "topics_in" in answer:
				answer["topics_in"] = []
				
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
				print("ALTER GO", new_selection_start, new_selection_end)
				topic_id = int(POST["topic_id"])
				if not topic_id in answer["topics_in"]:
					answer["topics_in"].append(topic_id)
				
				selections = [x for x in answer["selections"] if (x[0] >= new_selection_end or x[1] <= new_selection_start)]
				if topic_id != -1:
					selections.append([new_selection_start, new_selection_end, topic_id])
				selections.sort()
				answer["selections"] = selections
			elif POST["action"] == "topic_use":
				print("ALTER TOPIC USE")
				topic_id = int(POST["topic_id"])
				if not topic_id in answer["topics_in"]:
					answer["topics_in"].append(topic_id)
			elif POST["action"] == "topic_not_use":
				topic_id = int(POST["topic_id"])
				if topic_id in answer["topics_in"]:
					answer["topics_in"].remove(topic_id)
			
			if "scroll_top" in POST:
				answer["scroll_top"] = POST["scroll_top"]
			
		self.answer = json.dumps(answer)
		self.save()
		
	def finalize(self, POST):
		answer = json.loads(self.answer) 
		if self.problem.type == "segmentation":
			selections = answer["selections"]
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
				if len(terms) > 0:
					assessed_segments.append([terms, topic_id])
					segment = Segmentation_TypicalSegment.get_segment(self.problem, terms)
					segment.add_topic(topic_id)
					
			answer["terms_assessions"] = terms_assessions
			answer["assessed_segments"] = assessed_segments
			
		self.answer = json.dumps(answer)
		self.save()
		
	def __str__(self):
		if self.problem.type == "segmentation":
			return self.document.title
		else:
			return "task " + str(self.id)
		 
	def get_duration(self): 
		if self.completion_time:
			dt = self.completion_time - self.creation_time
		else: 
			dt = datetime.now() - self.creation_time
		seconds = dt.seconds
		return "{:02}:{:02}".format(seconds // 60, seconds % 60)
		
class ProblemAssessor(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False)
	assessor = models.ForeignKey(User, null=False)
	
	class Meta:
		unique_together = ('problem', 'assessor')
	
from django.contrib import admin
admin.site.register(AssessmentProblem)



### Specific models for segmentation assessment

class Segmentation_Topic(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False)
	name = models.TextField(null=False, default="")
	description = models.TextField(null=True)
		
	def description_html(self):
		return self.description.replace("\n","<br>")
	
	def description_lines(self):
		return self.description.split("\n")
		
		
class Segmentation_TypicalSegment(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False, default=0)
	first_term_id = models.IntegerField(null=False, default=0)
	terms = models.TextField(null=False, default="")
	topics = models.TextField(null=False, default="")
	
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