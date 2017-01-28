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
		#print("IN")
		self.prepare_log()
		self.log("Loading dataset " + self.text_id + "...")
		dataset_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		uci_folder = os.path.join(dataset_path, "UCI")
		vocab_file = os.path.join(uci_folder, "vocab." + self.text_id + ".txt")
		
		Term.objects.filter(dataset = self).delete()
		Document.objects.filter(dataset = self).delete()
		Modality.objects.filter(dataset = self).delete()
		TermInDocument.objects.filter(dataset = self).delete()
		from models.models import ArtmModel	
		ArtmModel.objects.filter(dataset = self).delete()
		
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
		dictionary.gather(batches_folder, vocab_file_path = vocab_file)
		dictionary.save_text(dictionary_file_name)
		
		
		
		
		

		
		# Loading dictionary
		self.log("Loading ARTM dictionary...")
		term_modality_index = np.full(1000000,-1).astype(int)
		term_index_id = -2
		modality_index_id = 0
		modalities_index = dict() 
		with open(dictionary_file_name, "r", encoding = 'utf-8') as f:
			for line in f:
				term_index_id += 1
				if term_index_id <= 0:
					continue
				parsed = line.replace(',',' ').split()
				term = Term()
				term.dataset = self
				term.text = parsed[0]
				term.index_id = term_index_id
				term.token_value = float(parsed[2])
				term.token_tf = int(parsed[3].split('.')[0])
				term.token_df = int(parsed[4].split('.')[0]) 
				modality_name = parsed[1]
				if not modality_name in modalities_index:
					modality = Modality()
					modality_index_id += 1
					modality.index_id = modality_index_id
					modality.name = modality_name
					modality.dataset = self 
					modality.save()
					modalities_index[modality_name] = modality 
				modality = modalities_index[modality_name] 
				term_modality_index[term_index_id] = modality.index_id
				term.modality = modality
				modality.terms_count += 1
				
				term.save() 
				if term_index_id % 10000 == 0:
					self.log(str(term_index_id))
					print(term_index_id)
					
					
		self.log("Saving modalities...")
		max_modality_size = 0
		word_modality_id = -1
		for key, modality in modalities_index.items():
			if modality.terms_count > max_modality_size:
				word_modality_id = modality.id
				max_modality_size = modality.terms_count
				
		for key, modality in modalities_index.items():
			if modality.id == word_modality_id:
				modality.is_word = True
			if 'tag' in modality.name:
				modality.is_tag = True
			modality.save()

					 
			 
		# Reading documents entries
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
						self.log("Warning! Time isn't provided.")
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
			cur_bow.add_term(term_index_id, term_count, term_modality_index[term_index_id])
		
		if cur_doc_id != self.documents_count + 1:
			raise ValueError("Fatal error! Promised " + str(self.documents_count) + "documents, by provided " + str(cur_doc_id) + ".")
		 
		
		
		self.log("Loaded " + str(self.documents_count) + " documents.")
		
		
		# Creating folder for models
		model_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id, "models")
		if not os.path.exists(model_path): 
			os.makedirs(model_path) 
		
		self.log("Dataset " + self.text_id + " loaded.")
		self.creation_time = datetime.now()
		self.status = 0
		self.save() 
	
	def reload_untrusted(self):
		try:
			self.reload()
		except:
			import traceback
			self.error_message = traceback.format_exc()
			self.status = 2
			self.save()
		
	def upload_from_archive(self, archive):
		archive_name = str(archive)
		parsed = archive_name.split('.')
		if parsed[1] != 'zip':
			raise ValueError("Must be zip archive")
		self.text_id = parsed[0]
		self.name = parsed[0]
		
		if len(Dataset.objects.filter(text_id = parsed[0])) != 0:
			raise ValueError("Dataset " + parsed[0] + " already exists.")
		zip_file_name = os.path.join(self.get_folder(), archive_name)
		with open(os.path.join(self.get_folder(), archive_name), 'wb+') as f:
			for chunk in archive.chunks():
				f.write(chunk)
		print("Archive unloaded.")
		
		import zipfile
		zip_ref = zipfile.ZipFile(zip_file_name, 'r')
		zip_ref.extractall(self.get_folder())
		zip_ref.close() 
		print("Archive unpacked. Dataset name: " + self.text_id)
		
		
		
	def get_batches(self):
		dataset_path = os.path.join(settings.DATA_DIR, "datasets", self.text_id)
		batches_folder = os.path.join(dataset_path, "batches")
		dictionary_file_name = os.path.join(batches_folder, "dict.txt")
		
		batch_vectorizer = artm.BatchVectorizer(data_path = batches_folder, data_format = "batches")
		dictionary = artm.Dictionary(name="dictionary")
		dictionary.load_text(dictionary_file_name)
		return batch_vectorizer, dictionary
		 
		 
	def get_tag_index(self):
		return np.load(os.path.join(settings.DATA_DIR, "datasets", self.text_id, "tgi.npy"))
	
	
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
	tags_string = models.TextField(null=True)
	 	
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
		right = len(bow) // 7
		while True:
			pos = (left + right) // 2
			bow_iid = struct.unpack('I', bow[7 * pos : 7*pos+4])[0]
			if bow_iid == iid:
				return struct.unpack('H', bow[7*pos+4 : 7*pos+6])[0]
			elif bow_iid > iid:
				right = pos
			else:
				left = pos + 1
			if left >= right:
				return 0
	
	def fetch_tags(self):
		tag_modalities = Modality.objects.filter(dataset = self.dataset, is_tag = True)
		if len (tag_modalities) == 0:
			return []
			
		tag_names = dict()
		tag_strings = dict()
		
		for modality in tag_modalities:
			tag_names[modality.index_id] = modality.name
			 
		bow = self.bag_of_words
		unique_terms_count = len(bow) // 7 
		
		for i in range(unique_terms_count):
			bow_iid = struct.unpack('I', bow[7*i : 7*i+4])[0]
			modality_iid = struct.unpack('B', bow[7*i+6 : 7*i+7])[0]
			if modality_iid in tag_names:
				term = Term.objects.filter(dataset = self.dataset, index_id = bow_iid)[0]
				if modality_iid in tag_strings:
					tag_strings[modality_iid] += ', '
				else:
					tag_strings[modality_iid] =''
				tag_strings[modality_iid] += '<a href="/term?id=' + str(term.id) + '">' + term.text + '</a>' 
				
		ret = []
		for tag_id, tag_string in tag_strings.items():
			ret.append({"name": tag_names[tag_id], "string": tag_string})
		return ret
		
	def fetch_bow(self, cut_bow):
		bow = self.bag_of_words
		unique_terms_count = len(bow) // 7 		
		bow_entries = []
		for i in range(unique_terms_count):
			bow_iid = struct.unpack('I', bow[7*i : 7*i+4])[0]
			bow_count = struct.unpack('H', bow[7*i+4 : 7*i+6])[0]
			bow_entries.append((-bow_count, bow_iid))
		bow_entries.sort()
		bow_send = ""
		prfx = "<a href = '/term?ds=" + str(self.dataset.id) + "&iid="
		rest = unique_terms_count
		for x in bow_entries:
			cnt = -x[0]
			iid = x[1]
			if cnt <= cut_bow:
				bow_send += str(rest) + " terms, which occured " + str(cut_bow) + " times or less, aren't shown." 
				break
			bow_send += prfx + str(iid) + "'>" + Term.objects.filter(dataset = self.dataset, index_id = iid)[0].text + "</a>: " + str(cnt) + "<br>"
			rest -= 1
		
		return bow_send
	
	def get_text(self):
		if self.dataset.text_provided:
			file_name = os.path.join(settings.DATA_DIR, "datasets", document.dataset.text_id, "documents", str(document.index_id) + ".txt")
			with open(file_name, encoding = "utf-8") as f:
				return f.read().replace("\n","<br>")
		else:
			return "Text wasn't provided"
	
	def __str__(self):
		return self.title
		 
class Modality(models.Model):
	name = models.TextField(null=False)
	dataset = models.ForeignKey(Dataset, null = False)
	terms_count = models.IntegerField(null = False, default = 0)
	index_id = models.IntegerField(null = False, default = 0)
	is_word = models.BooleanField(null = False, default = False)
	is_tag = models.BooleanField(null = False, default = False)
	def __str__(self):
		return self.dataset.name + "/" + self.name
		
class Term(models.Model):
	text = models.TextField(null=False)
	modality =  models.ForeignKey(Modality, null = False)
	dataset = models.ForeignKey(Dataset, null = False)
	index_id = models.IntegerField(null = False)				#id in UCI files and word_index files 
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
		
	def add_term(self, word_id, count, modality_index_id):
		self.bow[word_id] = (count, modality_index_id)
		
	def to_bytes(self):
		ret = bytes()
		for word_id, x in sorted(self.bow.items()):
			ret += struct.pack('I', word_id) + struct.pack('H', x[0]) + struct.pack('B', x[1])
		return ret
