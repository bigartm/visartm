from django.db import models
from datasets.models import Dataset, Term, Document, Modality
from django.contrib.auth.models import User
from datetime import datetime
import os
from django.conf import settings
import json
import numpy as np
import pandas as pd 
from scipy.spatial.distance import euclidean, cosine
from scipy.stats import entropy 
import artm
import re
from shutil import rmtree 
from django.db import transaction
import traceback
import struct


class ArtmModel(models.Model):
	dataset = models.ForeignKey(Dataset, null = False)
	creation_time = models.DateTimeField(null=False, default = datetime.now)
	text_id = models.TextField(null=False, default = "")
	#main_modality = models.ForeignKey(Modality, null = True)
	name = models.TextField(null=True)
	author = models.ForeignKey(User, null=True)
	layers_count = models.IntegerField(default = 1) 
	topics_count = models.TextField(null = False, default = "")
	status = models.IntegerField(null = False, default = 0) 
	error_message = models.TextField(null=True) 
	threshold = models.IntegerField(null = False, default = 100) 
	
	def __str__(self):
		if self.name == '':
			return "model " + str(self.id)
		else: 
			return self.name		
	
	def create_generic(self, POST):
		mode = POST['mode']
		self.log("Creating model, mode=" + mode)
		self.text_id = str(self.id) 
		
		try:
			if mode == 'flat': 
				iter_count = int(POST.getlist('iter_count')[0])
				self.layers_count = 1
				self.topics_count = "1 " + POST.getlist('num_topics')[0]
				self.save()
				artm_object = self.create_simple(iter_count = iter_count)
				self.save_matrices(artm_object)
			elif mode == "hier":
				self.layers_count = int(POST['num_layers'])
				iter_count = int(POST.getlist('iter_count')[1]) 
				self.topics_count = "1 " + ' '.join([POST.getlist('num_topics')[i + 1] for i in range(self.layers_count)])
				self.save()
				artm_object = self.create_simple(iter_count = iter_count)
				self.save_matrices(artm_object)
			elif mode == "script":
				script_file_name = os.path.join(settings.DATA_DIR, "scripts", POST['script_name'])
				with open(script_file_name) as f:
					code = compile(f.read(), script_file_name, "exec")		
				batch_vectorizer, dictionary = self.dataset.get_batches()
				local_vars = {"batch_vectorizer": batch_vectorizer, "dictionary": dictionary}  
				print("Running custom sript...")		
				exec(code, local_vars)
				print("Custom script finished.")
				artm_object = local_vars["model"]
				self.save_matrices(artm_object)
			elif mode == "custom":
				raise Exception("You cannot upload scripts.")
			elif mode == "matrices":
				self.text_id = POST["matrices_folder"]
			elif mode == "empty":
				sample_script_file = os.path.join(self.get_folder(), "sample.py")
				batches_folder = os.path.join(self.dataset.get_folder(), "batches")
				dictionary_file = os.path.join(batches_folder, "dict.txt")
				text =  "import artm\n" + \
					    "batch_vectorizer = artm.BatchVectorizer(data_path = '" + batches_folder + "', data_format = 'batches')\n" + \
						"dictionary = artm.Dictionary()\n" + \
				        "dictionary.load_text('" + dictionary_file + "')\n" + \
						"model = artm.ARTM(num_document_passes=10, num_topics = 9, cache_theta=True)\n" + \
						"model.initialize(dictionary = dictionary)\n" + \
						"model.fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = 10)\n" + \
						"model.get_phi().to_pickle('" + os.path.join(self.get_folder(), "phi") + "')\n" + \
						"model.get_theta().to_pickle('" + os.path.join(self.get_folder(), "theta") + "')\n" 
				
				with open(sample_script_file, "w") as f:
					f.write(text.replace("\\","\\\\"))
				self.status = 3
				self.save()
				return
			else:
				raise Exception('Unknown mode: ' + mode)
				
			self.reload()
		except:
			self.error_message = traceback.format_exc()
			self.status = 2
			self.save()
	
	def create_simple(self, iter_count):
		self.log("Creating simple model...")
		layers_count = self.layers_count 
		num_topics = [int(x) for x in self.topics_count.split()]
		
		batch_vectorizer, dictionary = self.dataset.get_batches()
		
		model = artm.hARTM(num_document_passes = iter_count)
		model.cache_theta = True
		layers = [0 for i in range(layers_count)]

		layers[0] = model.add_level(num_topics = num_topics[1],
                            topic_names=["topic" + str(t) for t in range(num_topics[1])] )
		layers[0].initialize(dictionary=dictionary)
		self.log("Layer 0 initialized.")
		layers[0].fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = iter_count)   
		self.log("Layer 0 fitted.")
		
		for layer_id in range(1, layers_count):
			layers[layer_id] = model.add_level(
				parent_level_weight = 0.1, 
				num_topics = num_topics[layer_id + 1],
				topic_names=["topic" + str(t) for t in range(num_topics[layer_id + 1])]
			)
			layers[layer_id].initialize(dictionary=dictionary)
			self.log("Layer " + str(layer_id) + " initialized.")
			layers[layer_id].fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = iter_count)  
			self.log("Layer " + str(layer_id) + " fitted.")
			
		self.log("Model built.")
		return model
		
	
	def save_matrices(self, artm_object):
		self.log ("Saving matrices for model " + str(self.id) + "...")
		# vocab_file = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "UCI", "vocab." + self.dataset.text_id + ".txt")
		
		self.log ("Saving matrix theta...") 
		artm_object.get_theta().to_pickle(os.path.join(self.get_folder(), "theta"))
		
		self.log("Saving matrix phi...") 
		artm_object.get_phi().to_pickle(os.path.join(self.get_folder(), "phi"))
		 
		is_hierarchial = True
		try:
			layers = artm_object._levels
		except:
			is_hierarchial = False
		
		if is_hierarchial and len(layers) == 1:
			is_hierarchial = False
		
		if is_hierarchial: 
			print("Saving matrices psi...")
			for layer_id in range(1, self.layers_count): 
				psi = layers[layer_id].get_psi().to_pickle(os.path.join(self.get_folder(), "psi" + str(layer_id)))
		
	def gather_phi(self):
		self.log("Loading matrix phi...")
		phi_path = os.path.join(self.get_folder(), "phi")
		if os.path.exists(phi_path):
			phi_raw = pd.read_pickle(os.path.join(self.get_folder(), "phi"))
			if phi_raw.shape[0] == self.dataset.terms_count:
				self.log("Considering that rows in phi are indexed according to dictionary.")
				phi = phi_raw.values
			else: 
				self.log("WARNING! Not all words are in phi. Will restore. In case of equal terms result can be wrong.")
				topics_count = phi_raw.shape[1]
				phi = np.zeros((self.dataset.terms_count, topics_count))
				terms_index = self.dataset.get_terms_index()
				for row in phi_raw.iterrows():
					term_text = row[0]
					try:
						term_matrix_id = terms_index[term_text] - 1
					except:
						self.log("WARNING! Word " + term_text + " don't belong to dataset dictionary.")
						continue
					for j in range(topics_count):
						phi[term_matrix_id][j] = row[1][j]
		else:
			self.log("WARNING! Phi wasn't detected. Will try load from matrices for modalities.")
			for modality in Modality.objects.get(dataset=self.dataset):
				phi_path = os.path.join(self.get_folder(), "phi_" +  modality.name)
				if os.path.exists(phi_path):
					self.log("Found matrix for modality " + modality.name + ". Will load.")
					terms_index = self.dataset.get_terms_index(modality=modality)
					for row in phi_raw.iterrows():
						term_text = row[0]
						try:
							term_matrix_id = terms_index[term_text] - 1
						except:
							self.log("WARNING! Word " + term_text + " don't belong to dataset dictionary.")
							continue
						for j in range(topics_count):
							phi[term_matrix_id][j] = row[1][j]
				else:
					self.log("Matrix for modality " + modality.name + " wasn't found.")
		self.log("Matrix phi loaded.")
		np.save(os.path.join(self.get_folder(), "phi.npy"), phi)
		self.log("Matrix phi saved in numpy format.")
				
	@transaction.atomic
	def reload(self):  
		vocab_file = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "UCI", "vocab." + self.dataset.text_id + ".txt")
		self.log("Reloading model " + str(self.id) + "...")
		
		# Loading matrices
		self.gather_phi()
		phi = np.load(os.path.join(self.get_folder(), "phi.npy"))
		phi_t = phi.transpose()
			
		self.log("Loading matrix theta...")
		theta_raw = pd.read_pickle(os.path.join(self.get_folder(), "theta")) #.sort_index(axis = 1)
		theta = theta_raw.values
		np.save(os.path.join(self.get_folder(), "theta.npy"), theta)	
		theta_t = theta.transpose()
		
		layers_count = self.layers_count
		if layers_count > 1:
			self.log("Loading matrix psi...")
			psi = [0 for i in range(layers_count)]		
			for i in range(1, self.layers_count):
				psi[i] = pd.read_pickle(os.path.join(self.get_folder(), "psi" + str(i))).values
				np.save(os.path.join(self.get_folder(), "psi"+ str(i) + ".npy"), psi[i])
		
		self.log("Counting topics...")			
		if layers_count == 1: 
			self.topics_count = "1 "  + str(theta.shape[0])
		else:		
			self.topics_count = "1 " + str(psi[1].shape[1])
			for layer_id in range(1, layers_count):  
				self.topics_count += " " + str(psi[layer_id].shape[0])
		
		terms_count = self.dataset.terms_count
		documents_count = self.dataset.documents_count		
		topics_count = [int(x) for x in self.topics_count.split()]
		total_topics_count = sum(topics_count)-1
		
		# Extracting topic names from theta index
		topic_names = [[] for i in range(layers_count + 1)]
		offset = 0
		for layer_id in range(1, layers_count + 1):
			topic_names[layer_id] = theta_raw.index[offset : offset + topics_count[layer_id]]
		offset += topics_count[layer_id]
		
		# Building temporary index for terms
		self.log("Building temporary index for words...")
		terms_index = Term.objects.filter(dataset = self.dataset).order_by("index_id") 
		terms_id_index = [term.id for term in terms_index]
		
		# Removing existing topics and related objects
		from visual.models import GlobalVisualization
		Topic.objects.filter(model = self).delete()
		TopTerm.objects.filter(model = self).delete()
		TopicInTopic.objects.filter(model = self).delete()
		GlobalVisualization.objects.filter(model = self).delete()
		
		
		
		# Creating topics, loading top terms, topic labeling
		self.log("Creating topics...")
		topics_index = [[] for i in range(layers_count + 1)]
		
		# Creating root topic
		root_topic = Topic()
		root_topic.model = self
		root_topic.index_id = 0
		root_topic.title = "root"
		root_topic.layer = 0
		root_topic.save()		
		
		topics_index[0].append(root_topic)		
		
		row_counter = 0
		for layer_id in range(1, layers_count + 1):
			for topic_id in range(topics_count[layer_id]):
				topic = Topic()
				topic.model = self
				topic.index_id = topic_id
				topic.layer = layer_id
				topic.save()
				
				# Top terms
				distr = phi_t[row_counter]
				row_counter += 1
				idx = np.zeros(terms_count)
				idx = np.argsort(distr)
				idx = idx[::-1]
				terms_to_title = []
				title_size = 3
				top_terms_size = 20
				ctr = 0
				for i in idx:
					term = terms_index[int(i)]
					if term.modality.is_word:
						ctr += 1
						top_term = TopTerm()
						top_term.model = self
						top_term.topic = topic
						top_term.term_id = terms_id_index[int(i)]
						top_term.weight = distr[int(i)]
						top_term.save()
						
						if ctr <= title_size:
							terms_to_title.append(term.text)
						if ctr == top_terms_size:
							break
				
				if 'topic' in topic_names[layer_id][topic_id]:
					topic.title = ', '.join(terms_to_title)
					topic.title_multiline = '\n'.join(terms_to_title)
				else:
					topic.title = topic_names[layer_id][topic_id]
					topic.title_multiline = '\n'.join(topic.title.split())
					
				topic.title_short = topic.title[0:20]			
				topic.save()
				
				topics_index[layer_id].append(topic)
				 
					
				
				if row_counter % 10 == 0:
					self.log("Created topic %d/%d." % (row_counter, total_topics_count))
		
		# Adding topics of top layer as children of root
		for topic in topics_index[1]:
			relation = TopicInTopic()
			relation.model = self
			relation.parent = root_topic
			relation.child = topic
			relation.save()
		
		threshold = self.threshold / 100.0
		
		# Building topics hierarchy
		for bottom_layer in range (2, layers_count + 1):
			top_layer = bottom_layer - 1
			self.log("Building topics hierarchy between layers %d and %d" % (top_layer, bottom_layer))
			for bottom_topic_id in range(topics_count[bottom_layer]):
				best_top_topic_id = np.argmax(psi[top_layer][bottom_topic_id])
				relation = TopicInTopic()
				relation.model = self
				relation.parent = topics_index[top_layer][best_top_topic_id]
				relation.child = topics_index[bottom_layer][bottom_topic_id]
				relation.save()
				
				if self.threshold <= 50:
					for top_topic_id in range(topics_count[top_layer]):
						if psi[top_layer][bottom_topic_id][top_topic_id] > threshold and top_topic_id != best_top_topic_id:
							relation = TopicInTopic()
							relation.model = self
							relation.parent = topics_index[top_layer][top_topic_id]
							relation.child = topics_index[bottom_layer][bottom_topic_id]
							relation.save()
			
		
		# Loading temporary reference for documents
		documents_index = Document.objects.filter(dataset = self.dataset).order_by("index_id")
 
		
		
		#Extracting documents in topics
		self.log("Extracting documents in topics...")
		theta_t_low = theta_t[:, total_topics_count - topics_count[layers_count] : total_topics_count]
		document_bags = [[] for i in range(topics_count[layers_count])]
		for doc_index_id in range(0, documents_count):
			#doc_id = documents_index[doc_index_id].id 
			distr = theta_t_low[doc_index_id]
			best_topic_id = distr.argmax()
			
			document_bags[best_topic_id].append((distr[best_topic_id], doc_index_id + 1))
			if self.threshold <= 50:
				for topic_id in range(topics_count[layers_count]):
					if distr[topic_id] > threshold and topic_id != best_topic_id:
						document_bags[topic_id].append(distr[topic_id], doc_index_id + 1)
			
			if doc_index_id % 1000 == 0:
				self.log(str(doc_index_id)) 
		
		
		self.log("Saving topics...")
		for topic_id in range(topics_count[layers_count]):
			topic = topics_index[layers_count][topic_id]
			topic.documents = bytes()
			document_bags[topic_id].sort(reverse = True)
			for weight, doc_index_id in document_bags[topic_id]:
				topic.documents += struct.pack('I', doc_index_id) + struct.pack('f', weight) 
			topic.documents_count = len(topic.documents) // 8
			topic.save()
		
		self.creation_time = datetime.now()
		self.arrange_topics()
		self.status = 0
		self.save()
		self.log("Model " + str(self.id) + " reloaded.")
		
	def reload_untrusted(self):
		try:
			self.reload()
		except:
			self.error_message = traceback.format_exc()
			self.status = 2
			self.save()
			
	def prepare_log(self):
		if len(self.text_id) == 0:
			self.text_id = str(self.id)
		self.log_file_name = os.path.join(self.get_folder(), "log.txt")
		with open(self.log_file_name, "w") as f:
			f.write("<br>\n")
			
	def log(self, string):
		if not settings.THREADING:
			print(string)
		with open(self.log_file_name, "a") as f:
			f.write(string + "<br>\n")
			
		
	def read_log(self):
		try:
			with open(os.path.join(self.get_folder(), "log.txt"), "r") as f:
				return f.read()
		except:
			return "Model is being processed..."
	
	# Only horizontal arranging
	@transaction.atomic
	def arrange_topics(self, mode = "alphabet"):
		# Counting horizontal relations topic-topic
		print("Counting horizontal relations topic-topic...")	
		phi = self.get_phi()
		phi_t = phi.transpose()
		layers_count = self.layers_count
		topics_count = [int(x) for x in self.topics_count.split()]
		topics_index = [[topic for topic in Topic.objects.filter(model = self, layer = i).order_by("index_id")]  for i in range(layers_count + 1)]
		
		
		
		TopicRelated.objects.filter(model = self).delete()
		topic_distances = [np.zeros((i, i)) for i in topics_count]
		shift = 0
		for layer_id in range (1, layers_count + 1):
			for i in range(topics_count[layer_id]):
				for j in range(topics_count[layer_id]):
					distance = euclidean(phi_t[shift + i], phi_t[shift + j])
					topic_distances[layer_id][i][j] = distance
			shift += topics_count[layer_id]
			
			for i in range(0, topics_count[layer_id]):
				idx = np.argsort(topic_distances[layer_id][i])
				for j in idx[1 : 1 + min(5, topics_count[layer_id] - 1)]:
					relation = TopicRelated()
					relation.model = self
					relation.topic1 = topics_index[layer_id][i]
					relation.topic2 = topics_index[layer_id][j]
					relation.weight = topic_distances[layer_id][i][j]
					relation.save()
		
		
		# Building topics spectrum
		for layer_id in range (1, layers_count + 1):
			self.log("Building topics spectrum for layer %d, mode=%s..." % (layer_id, mode))
			if mode == "alphabet":
				titles = [topics_index[layer_id][topic_id].title for topic_id in range(0, topics_count[layer_id])]
				idx = np.argsort(titles)
			if mode == "hamilton":
				from algo.topicarranging.Hamilton import HamiltonPath 
				hp = HamiltonPath(topic_distances[layer_id])
				idx = hp.solve()
			elif mode == "tsne": 
				from sklearn.manifold import TSNE
				tsne_model = TSNE(n_components = 1, random_state=0, metric = "precomputed")
				tsne_result = tsne_model.fit_transform(topic_distances[layer_id]).reshape(-1) 
				idx = np.argsort(tsne_result)
			i = 0
			for topic in topics_index[layer_id]:
				topic = topics_index[layer_id][idx[i]]
				topic.spectrum_index = i
				topic.save()
				i += 1
		self.status = 0
		self.save()
		
	

	 
	def get_folder(self):
		path = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "models", self.text_id)
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path	 
	 
	def get_visual_folder(self):
		path = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "models", self.text_id, "visual")
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path			

	def get_phi(self):
		return np.load(os.path.join(self.get_folder(), "phi.npy"))
	
	def get_theta(self):
		return np.load(os.path.join(self.get_folder(), "theta.npy"))
	
	def get_psi(self, i):
		return np.load(os.path.join(self.get_folder(), "psi" + str(i) + ".npy"))
	
	def lower_topics_count(self):
		return int(self.topics_count.split()[-1])
	
	
from django.db.models.signals import pre_delete
from django.dispatch import receiver
@receiver(pre_delete, sender=ArtmModel, dispatch_uid='artmmodel_delete_signal')
def remove_model_files(sender, instance, using, **kwargs):
	print("Now removing model " + str(instance.id))
	folder = instance.get_folder()
	print("Will delete folder " + folder)
	try:
		rmtree(folder)
	except:
		pass
				
class Topic(models.Model):
	model = models.ForeignKey(ArtmModel, null=False)
	index_id = models.IntegerField(null=True)
	title = models.TextField(null=False)
	title_short = models.TextField(null=True) 
	spectrum_index = models.IntegerField(null = True, default = 0) 
	layer = models.IntegerField(default = 1) 
	documents = models.BinaryField(null=True) #[4 bytes - document.id][4 bytes - weight]
	documents_count =  models.IntegerField(null=False, default=0)
	
	def __str__(self):
		return self.title
		
	def rename(self, new_title):
		self.title = new_title
		self.title_short = new_title[0:30]
		self.save()
		
	def get_documents(self): 
		all_documents = Document.objects.filter(dataset = self.model.dataset)
		ret = []
		for i in range(self.documents_count):
			doc_index_id = struct.unpack('I', self.documents[8*i : 8*i+4])[0]
			ret.append(all_documents.get(index_id = doc_index_id)) 
		return ret
		
	def get_documents_index_ids(self):  
		return [struct.unpack('I', self.documents[8*i : 8*i+4])[0] for i in range(self.documents_count)]
			
class TopicInDocument(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	document = models.ForeignKey(Document, null = False)
	topic = models.ForeignKey(Topic, null = False)
	probability = models.FloatField()
	def __str__(self):
		return str(self.topic) + " " + "{0:.1f}%".format(100 * self.probability)
		
class TopicInTopic(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	parent = models.ForeignKey(Topic, null = False, related_name = 'parent')
	child = models.ForeignKey(Topic, null = False, related_name = 'child')
	
		
		
class TopicRelated(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	topic1 = models.ForeignKey(Topic, null = False, related_name = 'fk1')
	topic2 = models.ForeignKey(Topic, null = False, related_name = 'fk2')
	weight = models.FloatField()
	def __str__(self):
		return str(self.topic2) + "{0:.1f}%".format(100 * self.weight)		

class TopicInTerm(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	topic = models.ForeignKey(Topic, null = False)
	term = models.ForeignKey(Term, null = False)
	weight = models.FloatField()
	def __str__(self):
		return str(self.term) + " " + str(self.topic) + "{0:.1f}%".format(100 * self.weight)		
		
class TopTerm(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	topic = models.ForeignKey(Topic, null = False)
	term =  models.ForeignKey(Term, null = False)
	weight = models.FloatField()
	def __str__(self):
		return str(self.term) + " (" + "{:10.4f}".format(self.weight) + " )"
	
from django.contrib import admin
admin.site.register(ArtmModel)
admin.site.register(Topic)