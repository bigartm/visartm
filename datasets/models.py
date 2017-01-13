from django.db import models 
from django.contrib.auth.models import User
import os
from django.conf import settings
import json
import logging
import datetime

class Dataset(models.Model):
	name = models.CharField('Name', max_length=50)
	text_id = models.TextField(unique=True, null=False)
	description = models.TextField('Description') 
	owner = models.ForeignKey(User, null=True, blank=True, default = None)
	time_provided = models.BooleanField(null=False, default=True)
	docs_count = models.IntegerField(default = 0)
	terms_count = models.IntegerField(default = 0) 
	
	def __str__(self):
		return self.name 
		
	def reload(self): 	 
		dataset_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		vocab_raw_file = os.path.join(dataset_path, "UCI", "vocab_raw." + self.text_id + ".txt")
		vocab_file = os.path.join(dataset_path, "UCI", "vocab." + self.text_id + ".txt")
		
		print("Loading dataset " + self.text_id + "...")
		
		# Removing all connected models
		from models.models import ArtmModel
		models = ArtmModel.objects.filter(dataset = self)
		for model in models:
			model.dispose()
		ArtmModel.objects.filter(dataset = self).delete()
		
		# Removing all terms
		Term.objects.filter(dataset = self).delete()
		
		# Vocabulary preprocessing (vocab_raw -> vocab) to make terms unique
		print("Vocabulary preprocessing...")
		with open(vocab_raw_file, "r", encoding = 'utf-8') as f:
			vocab_raw_lines = f.readlines()

		vocab_new_lines = []
			
		for line in vocab_raw_lines:
			parsed = line.split()
			vocab_new_lines.append(parsed[0] + "#"+ parsed[1] + " " + parsed[1] + "\n")
			
		with open(vocab_file, "w", encoding = 'utf-8') as f:
			f.writelines(vocab_new_lines)

		 
		# Loading modalities
		print("Loading modalities...")
		Modality.objects.filter(dataset = self).delete()
		modalities_set = set()
		modalities = dict()
		
		for word in vocab_raw_lines:
			modalities_set.add(word.split()[1])
		
		for modality in modalities_set:
			mod = Modality()
			mod.dataset = self
			mod.name = modality 
			mod.save()
			modalities[modality] = mod
		
		
		# Loading terms
		print("Loading terms...")
		Term.objects.filter(dataset = self).delete()
		i = 0
		for word in vocab_raw_lines:
			term = Term()
			term.dataset = self
			parsed = word.split()
			term.text = parsed[0]
			term.modality = modalities[parsed[1]]
			i += 1
			term.model_id = i
			term.text_id = parsed[0] + "#" + parsed[1]
			term.save()
			if (i % 1000 == 0):
				print (str(i))
		self.terms_count = i
		
		
		#Loading documents
		print("Loading documents...")
		Document.objects.filter(dataset = self).delete()
		docs_info_file = os.path.join(dataset_path, "documents.json")
		
		with open(docs_info_file) as f:
			docs_info = json.load(f)
			
		docs_count_ = 0
		for id, doc_info in docs_info.items():
			doc = Document()
			doc.title = doc_info["title"]
			
			if "snippet" in doc_info:
				doc.snippet = doc_info["snippet"]
 
			
			if "url" in doc_info:
				doc.url = doc_info["url"]
			
			if "time" in doc_info:
				lst = doc_info["time"]
				doc.time = datetime.datetime(lst[0], lst[1], lst[2], lst[3], lst[4], lst[5])
			
			doc.model_id = id
			doc.dataset = self
			doc.save()
			docs_count_ += 1
			
		self.docs_count = docs_count_
		self.save()
		
		print("Dataset " + self.text_id + " loaded.")
		 

class Document(models.Model):
	title = models.TextField(null=False)
	url = models.URLField(null=True)
	snippet = models.TextField(null=True)
	time = models.DateTimeField(null=True)
	model_id = models.IntegerField(null = False)
	dataset = models.ForeignKey(Dataset, null = False)
	
	class Meta:
		unique_together = (("dataset", "model_id"))
	
	def __str__(self):
		return self.title
		 
class Modality(models.Model):
	name = models.TextField(null=False)
	dataset = models.ForeignKey(Dataset, null = False)
	def __str__(self):
		return self.name
		
class Term(models.Model):
	text = models.TextField(null=False)
	modality =  models.ForeignKey(Modality, null = False)
	dataset = models.ForeignKey(Dataset, null = False)
	text_id = models.TextField(null=False)
	model_id = models.IntegerField(null = False)
	def __str__(self):
		return self.text
		
	
from django.contrib import admin
admin.site.register(Dataset)
admin.site.register(Document)
admin.site.register(Modality)
admin.site.register(Term)
