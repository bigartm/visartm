from django.db import models 
from django.contrib.auth.models import User
import os
from django.conf import settings
import json
import logging
from datetime import datetime
import artm
import numpy as np
from django.db import transaction
from shutil import rmtree

class Dataset(models.Model):
	name = models.CharField('Name', max_length=50)
	text_id = models.TextField(unique=True, null=False)
	description = models.TextField('Description') 
	owner = models.ForeignKey(User, null=True, blank=True, default = None)
	time_provided = models.BooleanField(null=False, default=True)
	docs_count = models.IntegerField(default = 0)
	terms_count = models.IntegerField(default = 0) 
	creation_time = models.DateTimeField(null=False, default = datetime.now)
	language = models.CharField(max_length = 20, default = 'undefined') 
	
	def __str__(self):
		return self.name 
		
	@transaction.atomic
	def reload(self): 	 
		print("Loading dataset " + self.text_id + "...")
		
		dataset_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		uci_folder = os.path.join(dataset_path, "UCI")
		vocab_file = os.path.join(uci_folder, "vocab." + self.text_id + ".txt")
		
		
		
		# Checking 
		term_count = np.zeros(1000000).astype(int)
		print("Checking...")
		docword_file = os.path.join(uci_folder, "docword." + self.text_id + ".txt")
		documents_count = 0
		with open(docword_file, "r") as f:
			lines = f.readlines()
		
		documents_count = int(lines[0]) 
		for line in lines[3:]:
			parsed = line.split()
			term_count[int(parsed[0])] += int(parsed[2])  
		
		for i in range (1, documents_count + 1):
			if term_count[i] == 0:
				raise ValueError("Document " + str(i) + " has no terms.")
		print("Check OK.")
		
		
		# Removing all connected models
		from models.models import ArtmModel
		models = ArtmModel.objects.filter(dataset = self)
		for model in models:
			model.dispose()
		ArtmModel.objects.filter(dataset = self).delete()
		
		# Removing all terms, documents and modalities
		Term.objects.filter(dataset = self).delete()
		Document.objects.filter(dataset = self).delete()
		Modality.objects.filter(dataset = self).delete()
		
		
		# Reading UCI vocabulary
		print("Reading UCI vocabulary...")
		terms_index = dict()
		modalities_index = dict()
		i = 1
		with open(vocab_file, "r", encoding = 'utf-8') as f:
			for line in f:
				parsed = line.split()
				term = Term()
				term.dataset = self
				term.text = parsed[0]
				term.index_id = i
				modality_name = parsed[1]
				terms_index[parsed[0] + "$#" + modality_name] = term
				if modality_name in modalities_index:
					term.modality = modalities_index[modality_name]
				else:
					modality = Modality()
					modality.name = modality_name
					modality.dataset = self
					modality.save()
					modalities_index[modality_name] = modality
					term.modality = modality
				i += 1
				if i % 10000 == 0:
					print(i)
				
		index_to_matrix = np.full(i,-1).astype(int)
		
		
		
		# Creating ARTM batches and dictionary
		print("Creating ARTM batches and dictionary...")
		batches_folder = os.path.join(dataset_path, "batches")
		dictionary_file_name = os.path.join(batches_folder, "dict.txt")
		if os.path.exists(batches_folder): 
			rmtree(batches_folder)
		os.makedirs(batches_folder)  
		batch_vectorizer = artm.BatchVectorizer(data_path = uci_folder, data_format = "bow_uci", batch_size = 1000,
								collection_name = self.text_id, target_folder = batches_folder)
		dictionary = artm.Dictionary(name="dictionary")
		dictionary.gather(batches_folder)
		dictionary.save_text(dictionary_file_name)
		
		
		# Loading dictionary
		print("Loading dictionary...")
		i = -3
		with open(dictionary_file_name, "r", encoding = 'utf-8') as f:
			for line in f:
				i += 1
				if i < 0:
					continue
				parsed = line.replace(',',' ').split()
				key = parsed[0] + "$#" + parsed[1]
				term = terms_index[key]
				term.matrix_id = i
				term.token_value = float(parsed[2])
				term.token_tf = int(parsed[3].split('.')[0])
				term.token_df = int(parsed[4].split('.')[0])
				index_to_matrix[term.index_id] = i
				term.save()
				if i % 10000 == 0:
					print(i)
			
		index_to_matrix_file_name = os.path.join(dataset_path, "itm.npy")
		np.save(index_to_matrix_file_name, index_to_matrix)
		
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
				doc.time = datetime(lst[0], lst[1], lst[2], lst[3], lst[4], lst[5])
			
			doc.model_id = id
			doc.dataset = self
			doc.save()
			docs_count_ += 1
			if docs_count_ % 1000 == 0:
				print(docs_count_)
			
		self.docs_count = docs_count_
		self.save() 
		 
		print("Dataset " + self.text_id + " loaded.")
		
	def get_batches(self):
		dataset_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		batches_folder = os.path.join(dataset_path, "batches")
		dictionary_file_name = os.path.join(batches_folder, "dict.txt")
		
		batch_vectorizer = artm.BatchVectorizer(data_path = batches_folder, data_format = "batches")
		dictionary = artm.Dictionary(name="dictionary")
		dictionary.load_text(dictionary_file_name)
		return batch_vectorizer, dictionary
		
	def get_index_to_matrix(self):
		return np.load(os.path.join(settings.DATA_DIR, "datasets", self.text_id, "itm.npy"))
		
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
	index_id = models.IntegerField(null = False)				#id in UCI files and word_index files
	matrix_id = models.IntegerField(default = -1, null = False)				#id in dictionary and phi matrix
	token_value = models.FloatField(default=0)
	token_tf = models.IntegerField(default=0)
	token_df = models.IntegerField(default=0)
	
	def __str__(self):
		return self.text
		
	
from django.contrib import admin
admin.site.register(Dataset)
admin.site.register(Document)
admin.site.register(Modality)
admin.site.register(Term)
