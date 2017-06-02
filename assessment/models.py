from django.db import models 
from datasets.models import Dataset, Document, Term
from models.models import ArtmModel, Topic
from django.contrib.auth.models import User	
from datetime import datetime, timedelta
import json
from random import randint
from django.conf import settings
import importlib

import algo.assessment.close_topics as ass_ct
from algo.assessment.segmentation import Segmentation_Topic, Segmentation_TypicalSegment

class AssessmentProblem(models.Model):
	modules = {}

	type = models.TextField() 
	dataset = models.ForeignKey(Dataset, null=False)
	model = models.ForeignKey(ArtmModel, null=True)
	layer = models.IntegerField(null=True, blank=True)
	
	description = models.TextField(null=False, default = "", blank=True)
	
	params = models.TextField(null=False, default = "{}")
	last_refreshed = models.DateTimeField(null=False, default=datetime.now) 
	timeout = models.IntegerField(null=False, default=1000000000)
	
	def __str__(self):
		return "#" + str(self.id) + " (" + self.dataset.name + "," + self.type \
			+ (","+ str(self.model) if self.model else "") \
			+ (",l"+ str(self.layer) if self.layer else "") \
			+ ")"
		
	def get_module(self):
		if self.type in AssessmentProblem.modules:
			return AssessmentProblem.modules[self.type]
		ret = importlib.import_module("algo.assessment." + self.type)
		AssessmentProblem.modules[self.type] = ret
		return ret

	# Get superviser/instructions view. Returns view context as dict.
	def get_view_context(self):
		context = self.get_module().get_problem_context(self)
		context["problem"] = self
		return context
	
	# Get superviser/instructions view. Returns view context as dict.
	def get_report_context(self):
		context = self.get_module().get_report_context(self)
		context["problem"] = self
		return context
			
	# Create Task instance, initialize it and save it	
	def create_task(self, request):
		self.refresh()
		task = self.get_module().create_task(self, request)
		if not task:
			return None
		task.problem = self
		task.status = 1
		task.assessor = request.user
		task.initialize()
		task.save()
		return task
	 
		
	# Allows superviser or assessor alter some global parameters of assessment problem
	def alter(self, request):
		if request.POST["action"] == "change_model":
			if len(AssessmentTask.objects.filter(problem=self)) > 0:
				raise ValueError("Cannot change model or layer, because some assessment are already made.")
			try:
				self.model = ArtmModel.objects.get(id=request.POST["model_id"])
			except:
				self.model = None
			try:
				layer = int(request.POST["layer"])
			except:
				layer = 1
			if self.model:
				if layer < 0 or layer > self.model.layers_count:
					raise ValueError("Layer doe not exist.")
				self.layer = layer
			self.save()
			self.get_module().initialize_problem(self)
		else:
			self.get_module().alter_problem(self, request)
		
	
	# Return number of completed and current task. Estimates how many tasks are to be done
	def count_tasks(self):
		try:
			estimate = self.get_module().estimate_tasks(self)
		except:
			estimate = "Unknown"
			
		return {
			"done" : len(AssessmentTask.objects.filter(problem=self, status=2)),
			"current" : len(AssessmentTask.objects.filter(problem=self, status=1)),
			"estimate" : estimate
		}
	
	# Return results as object
	def get_results(self):
		return self.get_module().get_problem_results(self)
		
		
    
	
	# Delete all 'dead' tasks
	def refresh(self):
		now = datetime.now()
		if (now - self.last_refreshed).seconds < 150:
			return 
		'''	
		deadline = now - timedelta(0, self.timeout)
		dead_tasks = AssessmentTask.objects.filter(problem=self, status=1, creation_time__lte=deadline)
		#for task in dead_tasks:
		#	task.status = 3
		#	task.save()
		dead_tasks.delete()
		'''
		self.last_refreshed = now
		self.save()
		
	def get_folder(self):
		if self.type == "segmentation":
			path = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "segmentation")
		else:
			path = os.path.join(settings.DATA_DIR, "assessment", str(self.id))
		
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path	 
		
	def can_assess(self, user):
		return len(ProblemAssessor.objects.filter(problem=self, assessor=user))!=0
			
	
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from shutil import rmtree 
@receiver(pre_delete, sender=AssessmentProblem, dispatch_uid='problem_delete_signal')
def remove_problem_files(sender, instance, using, **kwargs):
	# print("DELETE " + instance.get_folder())
	try:
		rmtree(instance.get_folder())
	except:
		pass
	

		
from contextlib import contextmanager		
import os
		
class AssessmentTask(models.Model):
	problem = models.ForeignKey(AssessmentProblem, null=False)
	assessor = models.ForeignKey(User, null=False, default=0)
	document = models.ForeignKey(Document, null = True)
	question = models.TextField(null = True)
	answer = models.TextField(null=False, default="{}")
	creation_time = models.DateTimeField(null=False, default = datetime.now) 
	completion_time = models.DateTimeField(null=True)
	status = models.IntegerField(null=False, default = 0)  # 1-issued, 2-completed
	 
	words_selected = models.IntegerField(default=0)
	segments_selected = models.IntegerField(default=0)
	
	
	# Get assessor view. Returns view context as dict.
	def get_view_context(self):		
		return self.problem.get_module().get_task_context(self)
		
		
	def initialize(self):
		self.problem.get_module().initialize_task(self)
			
		
	def alter(self, POST):
		self.problem.get_module().alter_task(self, POST)
			
		
	def finalize(self, POST):
		#print(str(POST))
		self.problem.get_module().finalize_task(self, POST)
		
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
