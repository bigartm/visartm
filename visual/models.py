from django.db import models
from datasets.models import Document
from models.models import ArtmModel, Topic, TopicInTopic
from datetime import datetime
import os
from django.conf import settings
import importlib
import traceback
from django.db import transaction
import json

class GlobalVisualization(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	name = models.TextField(null = False, default = 'none')
	status = models.IntegerField(null = False, default = 0)  # 0-processing; 1-ready; 2-error. 
	start_time = models.DateTimeField(null=False, default = datetime.now)
	finish_time = models.DateTimeField(null=True)
	error_message = models.TextField(null = False, default = "")
	
	def render(self):		
		self.model.log("Rendering visualization " + self.name + " for model " + str(self.model.id) + "...")
		params = self.name.split('_')
		# script_file_name = os.path.join(settings.BASE_DIR, "algo", "visualizations", params[0] + ".py") 
		visual_module = importlib.import_module("algo.visualizations." + params[0])
		
		# spec.loader.exec_module(visual_module)
		result = visual_module.visual(self, params)
	
		data_file_name = os.path.join(self.model.get_visual_folder(), self.name + ".txt")
		with open(data_file_name, "w", encoding = 'utf-8') as f:
			f.write(result)
		
		self.model.log("Render OK")
		self.error_message = "OK"
		self.finish_time = datetime.now()
		self.status = 1
		self.save()
		
	def render_untrusted(self):
		try:
			self.render()
		except:
			self.error_message = traceback.format_exc()
			self.status = 2
			self.finish_time = datetime.now()
			self.save()
			
from django.contrib import admin
admin.site.register(GlobalVisualization)

class Polygon(models.Model):
	vis = models.ForeignKey(GlobalVisualization, null=True, blank=True)
	points = models.TextField(null = True)
	rect_width = models.IntegerField(null=False, default = 0)
	rect_height = models.IntegerField(null=False, default = 0)
	rect_top = models.IntegerField(null=False, default = 0)
	rect_left = models.IntegerField(null=False, default = 0)
	parent = models.ForeignKey("self", null = True)
	#label = models.TextField(null = True)
	topic = models.ForeignKey(Topic, null = True) 
	document = models.ForeignKey(Document, null = True) 
	children_placed = models.BooleanField(null = False, default = False) 
 
	@transaction.atomic
	def place_children(self):
		if self.children_placed:
			return
		
		Polygon.objects.filter(parent = self).delete		
		polygons = []	 
			 
		if self.topic.layer == self.vis.model.layers_count:
			for document in self.topic.get_documents():
				polygon = Polygon() 
				self.vis.model.log("Adding polygon for document")
				polygon.vis = self.vis
				polygon.parent = self
				polygon.document = document 
				polygons.append(polygon)
		else:
			for relation in TopicInTopic.objects.filter(parent=self.topic):
				self.vis.model.log("Adding polygon for topic")
				polygon = Polygon()
				polygon.vis = self.vis
				polygon.parent = self
				polygon.topic = relation.child
				polygons.append(polygon)
			 
		if len(polygons) >= 1:
			self.partition(polygons)			
			for polygon in polygons: 
				polygon.save() 
		
		self.children_placed = True
		self.save()
	
	def partition(self, children):
		from math import floor, sqrt
		N = len(children)
		nh = int(round(sqrt(N * 1.0*self.rect_height / self.rect_width)))
		nw = int(floor(N / nh))
		d = N - nw * nh
		
		if N == 1:
			nh = 1
			nw = 1
			d = 0
			
		if d < 0 or d >= nh:
			raise ValueError("Unexpected.")
		
		# print("N=%d, nh=%d, nw=%d, d=%d" %(N,  nh, nw, d))
		
		dh = self.rect_height / nh
		
		ret = []
		ctr = 0
		for i in range(nh):
			cnw = nw
			if i < d:
				cnw +=1
			dw = self.rect_width / cnw
			for j in range(cnw):
				children[ctr].rect_top = self.rect_top + dh*i
				children[ctr].rect_left = self.rect_left + dw*j
				children[ctr].rect_width = dw
				children[ctr].rect_height = dh
				children[ctr].points_from_rect()
				children[ctr].save()	
				ctr += 1 
			
	def points_from_rect(self): 
		self.points = str(self.rect_left) + "," +  str(self.rect_top) + " " + \
					  str(self.rect_left + self.rect_width) + "," +  str(self.rect_top) + " " + \
		              str(self.rect_left + self.rect_width) + "," +  str(self.rect_top + self.rect_height) + " " + \
		              str(self.rect_left) + "," +  str(self.rect_top + self.rect_height);
		
	def to_json_object(self):
		ret = dict()
		ret["id"] = self.id 
		ret["rect"] = {"left": self.rect_left, "top":self.rect_top, "width":self.rect_width, "height":self.rect_height}
		ret["points"] = self.points
		if not self.topic is None:
			if self.topic.layer == 0:
				ret["label"] = self.topic.model.dataset.name
			else:
				ret["label"] = self.topic.title
		elif not self.document is None:
			ret["label"] = self.document.title 
			ret["docId"] = self.document.id
		
		return ret
		
		
		