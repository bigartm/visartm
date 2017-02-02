from django.db import models 
from datasets.models import Dataset, Document
from django.contrib.auth.models import User	
from datetime import datetime, timedelta
import json

class AssessmentProblem(models.Model):
	type = models.TextField() 
	dataset = models.ForeignKey(Dataset)
	params = models.TextField(null=False, default = "{}")
	last_refreshed = models.DateTimeField(null=False, default=datetime.now) 
	timeout = models.IntegerField(null=False, default=1800)
	
	def __str__(self):
		return self.dataset.name + "/" + self.type
	
	# Get superviser view
	def get_view_context(self):
		params = json.loads(self.params) 
		context = {"problem": self, "params": params}
		
		if self.type == "segments":
			pass 
		
		return context
	
	# Create Task instance, initialize it and save it	
	def create_task(self):
		task = AssessmentTask()
		if self.type == "segments":
			return None
			
		task.problem = self
		task.status = 1
		task.assessor = request.user
		task.save()
		return task
	
	# Allows superviser or assessor alter some global parameters of assessment problem
	def alter(self, POST):
		params = json.loads(self.params) 
		if self.type == "segments":
			if not "topics" in params:
					params["topics"] = []
				
			if "add_topic" in POST:
				target = POST["add_topic"]
				if len(target) > 2  and not target in params["topics"]:
					params["topics"].append(POST["add_topic"])
				
			if "delete_topic" in POST:
				target = POST["delete_topic"]
				if target in params["topics"]: 
					params["topics"].remove(POST["delete_topic"])
			
		self.params = json.dumps(params)
		self.save()
	
	# Merge all results in file
	def get_results(self, request):
		pass
		
		
	# Delete all 'dead' tasks
	def refresh(self):
		now = datetime.now()
		if (now - self.last_refreshed).seconds < 300:
			return
		deadline = now - timedelta(self.timeout)
		AssessmentTask.objects.filter(problem=self, status=1, creation_time__lte=deadline).delete()
		self.last_refreshed = now
		self.save()
			
	
	
class AssessmentTask(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False)
	assessor = models.ForeignKey(User, null=False, default=0)
	document = models.ForeignKey(Document, null = True)
	result = models.TextField()
	creation_time = models.DateTimeField(null=False, default = datetime.now) 
	completion_time = models.DateTimeField(null=True)
	status = models.IntegerField(null=False, default = 0)  # 1-issued, 2-completed
	
	# Get assessor view
	def get_view_context(self):
		context = dict()
		if self.type == "segments":
			document = self.document
	
		return context
	
	# Store assessed data (no save())
	def completed(self, POST):
		if self.type == "segments":
			pass
		
		task.completion_time = datetime.now()
		task.save()
		
class ProblemAssessor(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False)
	assessor = models.ForeignKey(User, null=False)
	
	class Meta:
		unique_together = ('problem', 'assessor')
	
from django.contrib import admin
admin.site.register(AssessmentProblem)
		
		
		
		
		
	