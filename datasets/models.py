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
import struct 

class Dataset(models.Model):
	name = models.CharField('Name', max_length=50)
	text_id = models.TextField(unique=True, null=False)
	description = models.TextField('Description') 
	owner = models.ForeignKey(User, null=True, blank=True, default = None)
	time_provided = models.BooleanField(null=False, default = False)
	text_provided = models.BooleanField(null=False, default = False)
	word_index_provided = models.BooleanField(null=False, default = False)
	uci_provided = models.BooleanField(null=False, default = False)
	json_provided = models.BooleanField(null=False, default = False)
	documents_count = models.IntegerField(default = 0)
	terms_count = models.IntegerField(default = 0) 
	creation_time = models.DateTimeField(null=False, default = datetime.now)
	language = models.CharField(max_length = 20, default = 'undefined') 
	status = models.IntegerField(null = False, default = 0) 
	error_message = models.TextField(null=True) 
	
	def __str__(self):
		return self.name 
		
	@transaction.atomic
	def reload(self): 	
		self.prepare_log()
		self.log("Loading dataset " + self.text_id + "...")
		dataset_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		uci_folder = os.path.join(dataset_path, "UCI")
		vocab_file = os.path.join(uci_folder, "vocab." + self.text_id + ".txt")
		Term.objects.filter(dataset = self).delete()
		Document.objects.filter(dataset = self).delete()
		Modality.objects.filter(dataset = self).delete()
		TermInDocument.objects.filter(dataset = self).delete()
		
		if self.json_provided:
			docs_info_file = os.path.join(dataset_path, "documents.json")
			with open(docs_info_file) as f:
				docs_info = json.load(f)
				
		if self.text_provided and not (self.word_index_provided and self.uci_provided):
			self.log("Parsing words ...")
			from algo.preprocessing.BowBuilder import BowBuilder
			builder = BowBuilder(self.text_id)
			builder.process()
			self.word_index_provided = True
			self.uci_provided = True
			
		
		#print("RUCIBOW")
		self.log("Reading UCI bag of words and creating documents...")		
		docword_file = os.path.join(uci_folder, "docword." + self.text_id + ".txt")
		with open(docword_file, "r") as f:
			lines = f.readlines()
		self.documents_count = int(lines[0]) 
		self.terms_count = int(lines[1])
		lines.append(str(self.documents_count + 1) + " 0 0")
		cur_doc_id = 1
		cur_bow = BagOfWords()
		cur_doc_terms_count = 0
		#entries_count = int(lines[2])
		bags = [bytes() for i in range(1 + self.documents_count)]
		for line in lines[3:]:
			parsed = line.split()
			doc_id = int(parsed[0])
			if doc_id != cur_doc_id:
				if doc_id - cur_doc_id != 1:
					print("R " + line)
					raise ValueError("Fatal error! Document " + str(cur_doc_id + 1) + " has no terms. Or docword file isn't sorted by docId.")
				doc = Document()
				doc.title = "document " + str(cur_doc_id)
				
				if self.json_provided:
					if cur_doc_id in docs_info:
						doc.fetch_meta(docs_info[cur_doc_id])
					elif str(cur_doc_id) in docs_info:
						doc.fetch_meta(docs_info[str(cur_doc_id)])
					else:
						self.log("Warning! No meta data in documents.json for document " + str(cur_doc_id) + ".")
					
					if self.time_provided and doc.time == None:
						self.log("Warning! Time isn't provided at least for document " + str(cur_doc_id) + ", but you promised that it will be.")
						self.time_provided = False
				
				doc.index_id = cur_doc_id
				doc.dataset = self
				doc.bag_of_words = cur_bow.to_bytes()
				doc.terms_count = cur_doc_terms_count
				doc.save() 
				#self.log("Create doc " + str(cur_doc_id))
				cur_bow = BagOfWords()
				cur_doc_terms_count = 0
				cur_doc_id = doc_id
			
				if cur_doc_id % 1000 == 0:
					self.log(str(doc_id)) 
					
			term_index_id = int(parsed[1])
			term_count = int(parsed[2])  
			cur_doc_terms_count += term_count
			cur_bow.add_term(term_index_id, term_count)
		
		if cur_doc_id != self.documents_count + 1:
			raise ValueError("Fatal error! Promised " + str(self.documents_count) + "documents, by provided " + str(cur_doc_id) + ".")
				
		
		# Removing all connected models
		from models.models import ArtmModel
		models = ArtmModel.objects.filter(dataset = self)
		for model in models:
			model.dispose()
		ArtmModel.objects.filter(dataset = self).delete()
		
		 
		# Reading UCI vocabulary
		self.log("Reading UCI vocabulary...")
		terms_index = dict()
		modalities_index = dict()
		modality_name = "@default_class"
		i = 1
		with open(vocab_file, "r", encoding = 'utf-8') as f:
			for line in f:
				parsed = line.split()
				term = Term()
				term.dataset = self
				term.text = parsed[0]
				term.index_id = i
				try:
					modality_name = parsed[1]
				except:
					pass
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
					self.log(str(i))
				
		index_to_matrix = np.full(i,-1).astype(int)
		
		
		
		# Creating ARTM batches and dictionary
		self.log("Creating ARTM batches and dictionary...")
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
		self.log("Loading ARTM dictionary...")
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
					self.log(str(i))
			
		index_to_matrix_file_name = os.path.join(dataset_path, "itm.npy")
		np.save(index_to_matrix_file_name, index_to_matrix)
		
		 

					 
		#self.log(str(self.documents_count))
		self.creation_time = datetime.now()
		self.status = 0
		self.save() 		
		
		
		# Creating folder for models
		model_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id, "models")
		if not os.path.exists(model_path): 
			os.makedirs(model_path) 
		
		self.log("Dataset " + self.text_id + " loaded.")
	
	def reload_untrusted(self):
		try:
			self.reload()
		except:
			import traceback
			self.error_message = traceback.format_exc()
			self.status = 2
			self.save()
		
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
		
	def check_can_load(self):
		#if not self.uci_provided:
		#	self.error_message = "Cannot load without UCI vocabulary and docword files."
		#	return False
		return True
		
	def prepare_log(self):
		self.log_file_name = os.path.join(settings.DATA_DIR, "datasets", self.text_id, "log.txt")
		with open(self.log_file_name, "w") as f:
			f.write("<br>\n")
			
	def log(self, string):
		with open(self.log_file_name, "a") as f:
			f.write(string + "<br>\n")
			
	def read_log(self):
		try:
			with open(os.path.join(settings.DATA_DIR, "datasets", self.text_id, "log.txt"), "r") as f:
				return f.read()
		except:
			return "Datased is reloading"
			
	def get_folder(self):
		path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path	 
	 
class Document(models.Model):
	title = models.TextField(null=False)
	url = models.URLField(null=True)
	snippet = models.TextField(null=True)
	time = models.DateTimeField(null=True)
	index_id = models.IntegerField(null = False)
	dataset = models.ForeignKey(Dataset, null = False)
	bag_of_words = models.BinaryField(null=False, default = bytes())
	terms_count = models.IntegerField(null = False, default = 0)
	
	class Meta:
		unique_together = (("dataset", "index_id"))
	
	def fetch_meta(self, doc_info):
		if 'title' in doc_info:
			self.title = doc_info["title"]
		
		if "snippet" in doc_info:
			self.snippet = doc_info["snippet"]
		
		if "url" in doc_info:
			self.url = doc_info["url"]
		 
		if "time" in doc_info:
			lst = doc_info["time"]
			try:
				self.time = datetime.fromtimestamp(lst)
			except:
				self.time = datetime(lst[0], lst[1], lst[2], lst[3], lst[4], lst[5])				
	
	def count_term(self, iid):
		bow = self.bag_of_words
		left = 0
		right = len(bow) // 6
		while True:
			pos = (left + right) // 2
			bow_iid = struct.unpack('I', bow[6 * pos : 6*pos+4])[0]
			if bow_iid == iid:
				return struct.unpack('H', bow[6*pos+4 : 6*pos+6])[0]
			elif bow_iid > iid:
				right = pos
			else:
				left = pos + 1
			if left >= right:
				return 0
		
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
	documents_indexed = models.BooleanField(null = False, default = False)

	def __str__(self):
		return self.text	
	
	@transaction.atomic
	def count_documents_index(self):
		if self.documents_indexed:
			return
			
		documents = Document.objects.filter(dataset = self.dataset)
		for document in documents:
			count = document.count_term(self.index_id)
			if count != 0:
				relation = TermInDocument()
				relation.dataset = self.dataset
				relation.term = self
				relation.document = document
				relation.count = count
				relation.save()
			
		self.documents_indexed = True
		self.save()
	
	
			
class TermInDocument(models.Model):
	dataset = models.ForeignKey(Dataset, null = False)
	term = models.ForeignKey(Term, null = False)
	document = models.ForeignKey(Document, null = False)
	count = models.IntegerField(default=0)

		
	
from django.contrib import admin
admin.site.register(Dataset)
admin.site.register(Document)
admin.site.register(Modality)
admin.site.register(Term)




class BagOfWords():
	def __init__(self):
		self.bow = dict()
		
	def add_term(self, word_id, count):
		self.bow[word_id] = count
		
	def to_bytes(self):
		ret = bytes()
		for word_id, count in sorted(self.bow.items()):
			ret += struct.pack('I', word_id) + struct.pack('H', count)
		return ret
