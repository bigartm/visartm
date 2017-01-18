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


class ArtmModel(models.Model):
	dataset = models.ForeignKey(Dataset, null = False)
	creation_time = models.DateTimeField(null=False, default = datetime.now)
	main_modality = models.ForeignKey(Modality, null = True)
	name = models.TextField(null=True)
	author = models.ForeignKey(User, null=True)
	layers_count = models.IntegerField(default = 1) 
	topics_count = models.TextField(null = True)
	status = models.IntegerField(null = False, default = 0) 
	
	def __str__(self):
		if self.name == '':
			return self.creation_time.strftime("%d.%m.%Y %H:%M")
		else: 
			return self.name		
	
	def create_simple(self, iter_count):
		print("Creating simple model...")
		layers_count = self.layers_count
		out_folder = os.path.join(settings.DATA_DIR, "models", str(self.id)) 
		num_topics = [int(x) for x in self.topics_count.split()]
		if not os.path.exists(out_folder):
			os.makedirs(out_folder)
		
		batch_vectorizer, dictionary = self.dataset.get_batches()
		
		model = artm.hARTM(num_document_passes = iter_count)
		model.cache_theta = True
		layers = [0 for i in range(layers_count)]

		layers[0] = model.add_level(num_topics = num_topics[1],
                            topic_names=[str(t) for t in range(num_topics[1])] )
		layers[0].initialize(dictionary=dictionary)
		print("Layer 0 initialized.")
		layers[0].fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = iter_count)   
		print("Layer 0 fitted.")
		
		for layer_id in range(1, layers_count):
			layers[layer_id] = model.add_level(
				parent_level_weight = 0.1, 
				num_topics = num_topics[layer_id + 1],
				topic_names=[str(t) for t in range(num_topics[layer_id + 1])]
			)
			layers[layer_id].initialize(dictionary=dictionary)
			print("Layer " + str(layer_id) + " initialized.")
			layers[layer_id].fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = iter_count)  
			print("Layer " + str(layer_id) + " fitted.")
			
		print("Model built.")
		return model
		
	
	def save_matrices(self, artm_object):
		print ("Saving matrices for model " + str(self.id) + "...")
		vocab_file = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "UCI", "vocab." + self.dataset.text_id + ".txt")
		model_path = os.path.join(settings.DATA_DIR, "models", str(self.id))
		if not os.path.exists(model_path):
			os.makedirs(model_path)
		
		print ("Saving matrix theta...") 
		theta_npy_file_name = os.path.join(model_path, "theta.npy") 
		theta_raw = artm_object.get_theta()
		theta = theta_raw.sort_index(axis = 1).values		
		np.save(theta_npy_file_name, theta)
		
		print("Saving matrix phi...") 
		phi_npy_file_name = os.path.join(model_path, "phi.npy")
		np.save(phi_npy_file_name, artm_object.get_phi().values)		
		
		
		is_hierarchial = True
		try:
			layers = artm_object._levels
		except:
			is_hierarchial = False
		
		if is_hierarchial and len(layers) == 1:
			is_hierarchial = False
		
		
		if is_hierarchial: 
			print("Saving matrices psi...")
			self.layers_count = len(layers)  			
			self.topics_count = "1"
			for layer_id in range(1, self.layers_count): 
				psi_file_name = os.path.join(model_path, "psi" + str(layer_id) + ".npy")
				psi = layers[layer_id].get_psi().values
				np.save(psi_file_name, psi)
				if layer_id == 1:
					self.topics_count += " " + str(psi.shape[1])
				self.topics_count += " " + str(psi.shape[0])
		else:
			self.topics_count = "1 "  + str(theta.shape[0])
			self.layers_count = 1
			
		self.save()
		
	def get_phi(self):
		return np.load(os.path.join(settings.DATA_DIR, "models", str(self.id), "phi.npy"))
	
	def get_theta(self):
		return np.load(os.path.join(settings.DATA_DIR, "models", str(self.id), "theta.npy"))
	
	@transaction.atomic
	def reload(self): 
		self.status = 0
		vocab_file = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "UCI", "vocab." + self.dataset.text_id + ".txt")
		model_path = os.path.join(settings.DATA_DIR, "models", str(self.id))
		print ("Reloading model " + str(self.id) + "...")
		
		# Loading matrices
		print ("Loading matrices...")
		layers_count = self.layers_count
			
		theta = self.get_theta()
		theta_t = theta.transpose()
		phi = self.get_phi()
		phi_t = phi.transpose()
		if layers_count > 1:
			psi = [0 for i in range(self.layers_count)]		
			for i in range(1, self.layers_count):
				psi[i] = np.load(os.path.join(model_path, "psi"+ str(i) + ".npy"))
		
		terms_count = self.dataset.terms_count
		documents_count = self.dataset.documents_count		
		topics_count = [int(x) for x in self.topics_count.split()]
		total_topics_count = sum(topics_count)-1
		
		# Building temporary index for terms
		print("Building temporary index for words...")
		terms_index = Term.objects.filter(dataset = self.dataset).order_by("matrix_id") 
		terms_id_index = [term.id for term in terms_index]
		
		# Removing existing topics and related objects
		from visual.models import GlobalVisualization
		Topic.objects.filter(model = self).delete()
		TopTerm.objects.filter(model = self).delete()
		TopicInTopic.objects.filter(model = self).delete()
		GlobalVisualization.objects.filter(model = self).delete()
		
		
		
		# Creating topics, loading top terms, topic labeling
		print("Creating topics...")
		topics_index = [[] for i in range(layers_count + 1)]
		
		# Creating root topic
		root_topic = Topic()
		root_topic.model = self
		root_topic.id_model = 0
		root_topic.title = "root"
		root_topic.layer = 0
		root_topic.save()		
		
		topics_index[0].append(root_topic)		
		
		row_counter = 0
		for layer_id in range(1, layers_count + 1):
			for topic_id in range(topics_count[layer_id]):
				topic = Topic()
				topic.model = self
				topic.id_model = topic_id
				topic.layer = layer_id
				distr = phi_t[row_counter]
				row_counter += 1
				idx = np.zeros(terms_count)
				idx = np.argsort(distr)
				idx = idx[::-1]
				
				
				terms_to_title = []
				title_size = 3
				cnt = 0
				for i in idx:
					term = terms_index[int(i)]
					if term.modality == self.main_modality:
						terms_to_title.append(term.text)
						cnt += 1
					if cnt == title_size:
						break
						
				topic.title = ', '.join(terms_to_title)
				topic.title_multiline = '\n'.join(terms_to_title)
				topic.title_short = topic.title[0:20]
				
				
				topic.save()
				topics_index[layer_id].append(topic)
				
				for i in idx[0:100]:
					top_term = TopTerm()
					top_term.model = self
					top_term.topic = topic
					top_term.term_id = terms_id_index[int(i)]
					top_term.weight = distr[int(i)]
					top_term.save()
				
				if row_counter % 10 == 0:
					print("Created topic %d/%d." % (row_counter, total_topics_count))
		
		# Adding topics of top layer as children of root
		for topic in topics_index[1]:
			relation = TopicInTopic()
			relation.model = self
			relation.parent = root_topic
			relation.child = topic
			relation.save()
			
		# Building topics hierarchy
		for bottom_layer in range (2, layers_count + 1):
			top_layer = bottom_layer - 1
			print("Building topics hierarchy between layers %d and %d" % (top_layer, bottom_layer))
			for bottom_topic_id in range(topics_count[bottom_layer]):
				top_topic_id = np.argmax(psi[top_layer][bottom_topic_id])
				relation = TopicInTopic()
				relation.model = self
				relation.parent = topics_index[top_layer][top_topic_id]
				relation.child = topics_index[bottom_layer][bottom_topic_id]
				relation.save()
		
		
		
		# Loading temporary reference for documents
		documents_index = Document.objects.filter(dataset = self.dataset).order_by("index_id")
		print("DC", documents_count)
		print("LDI", len(documents_index))
		
		
		#Extracting documents in topics
		print("Extracting documents in topics...")
		DocumentInTopic.objects.filter(model = self).delete()
		
		theta_t_low = theta_t[:, total_topics_count - topics_count[layers_count] : total_topics_count]
		
		
		for doc_id in range(0, documents_count):
			distr = theta_t_low[doc_id]
			topic_id = distr.argmax()
			relation = DocumentInTopic()
			relation.model = self
			relation.document = documents_index[doc_id]
			relation.topic = topics_index[layers_count][topic_id]
			topics_index[layers_count][topic_id].documents_count += 1
			relation.save()
			if doc_id % 1000 == 0:
				print(doc_id) 
		
		for topic_id in range(topics_count[layers_count]):
			topics_index[layers_count][topic_id].save()
		
		self.creation_time = datetime.now()
		self.save()
		
		
		
		print("Model " + str(self.id) + " reloaded.")
		self.arrange_topics()
		self.status = 1
	
	
	
	# Only horizontal arranging
	@transaction.atomic
	def arrange_topics(self, mode = "alphabet"):
		self.status = 0
		
		# Counting horizontal relations topic-topic
		print("Counting horizontal relations topic-topic...")	
		phi = self.get_phi()
		phi_t = phi.transpose()
		layers_count = self.layers_count
		topics_count = [int(x) for x in self.topics_count.split()]
		topics_index = [[topic for topic in Topic.objects.filter(model = self, layer = i).order_by("id_model")]  for i in range(layers_count + 1)]
		
		
		
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
			print("Building topics spectrum for layer %d, mode=%s..." % (layer_id, mode))
			if mode == "alphabet":
				titles = [topics_index[layer_id][topic_id].title for topic_id in range(0, topics_count[layer_id])]
				idx = np.argsort(titles)
			if mode == "hamilton":
				from algo.Hamilton import HamiltonPath 
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
		self.status = 1
			
	def dispose(self):
		model_path = os.path.join(settings.DATA_DIR, "models", str(self.id))
		try:
			rmtree(model_path)
		except:
			pass
	 
	def get_visual_folder(self):
		path = os.path.join(settings.DATA_DIR, "models", str(self.id), "visual")
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path							
				
class Topic(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	id_model = models.IntegerField(null = True)
	title = models.TextField(null=False)
	title_short = models.TextField(null=True) 
	spectrum_index = models.IntegerField(null = True, default = 0) 
	layer = models.IntegerField(default = 1) 
	documents_count = models.IntegerField(default = 0)
	
	def __str__(self):
		return self.title
		
	def rename(self, new_title):
		self.title = new_title
		self.title_short = new_title[0:30]
		self.save()
		
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
	
class DocumentInTopic(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	document = models.ForeignKey(Document, null = False)
	topic = models.ForeignKey(Topic, null = False) 
	def __str__(self):
		return str(self.document)
		
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