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
from algo.Hamilton import HamiltonPath
import re
from shutil import rmtree
from random import random
from sklearn.manifold import TSNE

class ArtmModel(models.Model):
	dataset = models.ForeignKey(Dataset, null = False)
	creation_time = models.DateTimeField(null=False, default = datetime.now)
	main_modality = models.ForeignKey(Modality, null = True)
	name = models.TextField(null=True)
	author = models.ForeignKey(User, null=True)
	layers_count = models.IntegerField(default = 1) 
	topics_count = models.TextField(null = True)
	status = models.TextField(null = True)
	status_code = models.IntegerField(null = False, default = 0) 
	
	def __str__(self):
		if self.name == '':
			return self.creation_time.strftime("%d.%m.%Y %H:%M")
		else: 
			return self.name		
	
	def create_simple(self, iter_count):
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
		theta_file_name = os.path.join(model_path, "theta")
		theta_npy_file_name = os.path.join(model_path, "theta.npy") 
		theta = artm_object.get_theta().sort_index(axis = 1).values		
		np.save(theta_npy_file_name, theta)
		
		print("Saving matrix phi...")
		phi_file_name = os.path.join(model_path, "phi")
		phi_npy_file_name = os.path.join(model_path, "phi.npy")
		phi_raw = artm_object.get_phi()
		words_reverse_index = dict()
		with open(vocab_file, "r", encoding = 'utf-8') as f:
			vocab_lines = f.readlines()
		words_count = len(vocab_lines)
		total_topics_count = phi_raw.shape[1]
		phi = np.zeros((words_count, total_topics_count))
		word_id = 0
		for line in vocab_lines:
			word = line.split()[0]
			try:
				series = phi_raw.loc[word]
				topic_id = 0
				for weight in series:
					phi[word_id][topic_id] = weight
					topic_id +=1
			except:
				pass
			word_id += 1
			if word_id % 10000 == 0:
				print (word_id)
		np.save(phi_npy_file_name, phi)		
		
		
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
	
	def reload(self):
		self.delete_visuals()
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
		documents_count = self.dataset.docs_count		
		topics_count = [int(x) for x in self.topics_count.split()]
		total_topics_count = sum(topics_count)-1
		
		# Building temporary index for terms
		print("Building temporary index for words...")
		terms_index = Term.objects.filter(dataset = self.dataset).order_by("model_id")
		terms_id_index = [term.id for term in terms_index]
		
		# Removing existing topics and related objects
		Topic.objects.filter(model = self).delete()
		TopTerm.objects.filter(model = self).delete()
		TopicInTopic.objects.filter(model = self).delete()
		
		
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
		documents_index = Document.objects.filter(dataset = self.dataset).order_by("model_id")
		
		
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
			relation.save()
			if doc_id % 1000 == 0:
				print(doc_id) 
		self.creation_time = datetime.now()
		self.save()
		print("Model " + str(self.id) + " reloaded.")
		self.arrange_topics("hamilton")
	
	
	# Only horizontal arranging
	def arrange_topics(self, mode = "alphabet"):
		self.delete_visuals()
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
				hp = HamiltonPath(topic_distances[layer_id])
				idx = hp.solve()
			elif mode == "tsne": 
				tsne_model = TSNE(n_components = 1, random_state=0, metric = "precomputed")
				tsne_result = tsne_model.fit_transform(topic_distances[layer_id]).reshape(-1) 
				idx = np.argsort(tsne_result)
				
			i = 0
			for topic in topics_index[layer_id]:
				topic = topics_index[layer_id][idx[i]]
				topic.spectrum_index = i
				topic.save()
				i += 1
			
	def dispose(self):
		model_path = os.path.join(settings.DATA_DIR, "models", str(self.id))
		try:
			rmtree(model_path)
		except:
			pass
			
	def build_circles(self, topic):
		answer = []
		if topic.layer == self.layers_count:
			relations = DocumentInTopic.objects.filter(topic = topic)
			for relation in relations:
				document = relation.document
				answer.append({"id": document.id, "size":1})
		else:
			relations = TopicInTopic.objects.filter(parent = topic)
			for relation in relations:
				child = relation.child
				answer.append({"name": child.title, "children": self.build_circles(child)})
		return answer
		
	def build_foamtree(self, topic):		
		answer = []
		if topic.layer == self.layers_count:
			relations = DocumentInTopic.objects.filter(topic = topic)
			for relation in relations:
				document = relation.document
				answer.append({"label": document.title, "id": document.id})
		else:
			relations = TopicInTopic.objects.filter(parent = topic)
			for relation in relations:
				child = relation.child
				answer.append({"label": child.title, "groups": self.build_foamtree(child)})
		return answer
		
	def build_tsne(self):
		print ("Buildig t-SNE visualization for model " + str(self.id) + "...") 
		tsne_matrix_path = os.path.join(self.get_visual_folder(), "tsne_matrix.npy")
		
		try:
			tsne_matrix = np.load(tsne_matrix_path)
			print ("t-SNE matrix from cache.")
		except:
			theta_t = self.get_theta().transpose()
			tsne_model = TSNE(n_components=2, random_state=0)
			print ("Fitting t-SNE...")
			tsne_matrix = tsne_model.fit_transform(theta_t)  
			print ("t-SNE fit.")
			np.save(tsne_matrix_path, tsne_matrix)
		
		answer = []
		documents = Document.objects.filter(dataset = self.dataset).order_by("model_id")
		documents_count = tsne_matrix.shape[0]
		
		border_0 = tsne_matrix[0].copy()
		border_1 = tsne_matrix[0].copy()
		
		print(border_0)
		for i in range(documents_count):
			border_0[0] = min(border_0[0], tsne_matrix[i][0])
			border_1[0] = max(border_1[0], tsne_matrix[i][0])
			border_0[1] = min(border_0[1], tsne_matrix[i][1])
			border_1[1] = max(border_1[1], tsne_matrix[i][1])
		print("min",border_0)
		print("max",border_1)
		
		
		i = 0
		for document in documents:
			answer.append({"X": (tsne_matrix[i][0] - border_0[0]) / (border_1[0] - border_0[0]), 
						   "Y": (tsne_matrix[i][1] - border_0[1]) / (border_1[1] - border_0[1]), 
						   "id": document.id})
			i += 1
			
		return "docs = " + json.dumps(answer) + ";\n"
	
	def get_visual(self, visual_name):
		file_name = os.path.join(self.get_visual_folder(), visual_name)
		if os.path.exists(file_name):
			with open(file_name, "r") as f:
				return f.read()
		
		root_topic = Topic.objects.filter(model = self, layer = 0)[0]
		
		result = ""
		if visual_name == "foamtree":
			result = json.dumps({"groups": self.build_foamtree(root_topic), "label": self.dataset.name})
		elif visual_name == "circles":
			result = json.dumps({"children": self.build_circles(root_topic)})
		elif visual_name == "temporal_dots":
			result = self.build_temporal_dots()
		elif visual_name == "tsne":
			result = self.build_tsne()
			
		with open(file_name, "w", encoding = 'utf-8') as f:
			f.write(result)
		return result 	
	
	def date_hash(self, date, group_by):
		if (group_by == "year"):
			return date.year
		if (group_by == "month"):
			return date.month + 100 * date.year
		elif (group_by == "day"):
			return date.day + 100 * date.month + 10000 * date.year
			
	def date_name(self, date_hash, group_by):
		if (group_by == "year"):
			return str(date_hash)
		if (group_by == "month"):
			return str(date_hash % 100) + "/" + str(int(date_hash / 100)) 
		elif (group_by == "day"):
			return str(date_hash % 100) + "/" + str( int(date_hash / 100) % 100) + "/" + str(int(date_hash / 1000000))  
	
		
	def get_visual_folder(self):
		path = os.path.join(settings.DATA_DIR, "models", str(self.id), "visual")
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path
		
	def delete_visuals(self, mode = "all"):
		if mode == "all":
			rmtree(self.get_visual_folder()) 
			
	def get_temporal_cells(self, group_by): 		
		file_name = os.path.join(self.get_visual_folder(), "temporal_cells_" + group_by + ".txt")
		if os.path.exists(file_name):
			with open(file_name, "r") as f:
				return f.read()
				
		doc_topics = DocumentInTopic.objects.filter(model = self)
		topics = Topic.objects.filter(model = self, layer = self.layers_count).order_by("spectrum_index")
		
		dates_hashes = set()
		for doc_topic in doc_topics:
			dates_hashes.add(self.date_hash(doc_topic.document.time, group_by))
		dates_hashes = list(dates_hashes)
		dates_hashes.sort()
		dates_send = []
		dates_reverse_index = dict()
		
		i = 0 
		for date_h in dates_hashes:
			dates_reverse_index[date_h] = i 
			dates_send.append({"X": i, "name": self.date_name(date_h, group_by)})
			i += 1
			
		cells = dict()
		
		
		
		for doc_topic in doc_topics:
			cell_xy = (dates_reverse_index[self.date_hash(doc_topic.document.time, group_by)], doc_topic.topic.spectrum_index)
			if not cell_xy in cells:
				cells[cell_xy] = []
			cells[cell_xy].append(doc_topic.document.id)
		
		max_intense = 0
		cells_send = []
		for key, value in cells.items():
			intense = len(value);
			max_intense = max(max_intense, intense)
			cells_send.append({"X" : key[0], "Y" : key[1], "intense": intense, "docs" : value})
		
		topics_send = [{"Y": topic.spectrum_index, "name": ' '.join(re.findall(r"[\w']+", topic.title)[0:2])} for topic in topics]
		
		# in case of hierarchical model we want show tree
		high_topics_send = []
		lines_send = []
		if self.layers_count > 1:
			high_topics = Topic.objects.filter(model = self, layer = self.layers_count - 1)
			high_topics_temp = []
			for topic in high_topics:
				children = TopicInTopic.objects.filter(parent = topic)
				positions = [relation.child.spectrum_index for relation in children]
				avg = sum(positions)/float(len(positions))
				high_topics_temp.append({"mass_center_y":avg, "name": ' '.join(re.findall(r"[\w']+", topic.title)[0:2]), "positions": positions})
			high_topics_temp.sort(key = lambda x: x["mass_center_y"])
			
			i = 0
			K = len(topics_send) / float(len(high_topics_temp))
			for el in high_topics_temp:		
				pos_y = K*(i+0.5)
				high_topics_send.append({"Y": pos_y, "name" : el["name"]})
				for j in el["positions"]:
					lines_send.append({"from_y": pos_y, "to_y": j})
				i += 1
		
		
		result = "cells=" + json.dumps(cells_send) + ";\n" + \
				"dates=" + json.dumps(dates_send) + ";\n" + \
				"topics=" + json.dumps(topics_send) + ";\n" + \
				"high_topics=" + json.dumps(high_topics_send) + ";\n" + \
				"lines=" + json.dumps(lines_send) + ";\n" + \
				"max_intense=" + str(max_intense) + ";\n"
				 
		with open(file_name, "w", encoding = 'utf-8') as f:
			f.write(result)
		return result
	
	def build_temporal_dots(self): 		 
		documents = Document.objects.filter(dataset = self.dataset)
		doc_topics = DocumentInTopic.objects.filter(model = self)		
		min_time = documents[0].time
		max_time = min_time
		
		for document in documents:
			time = document.time
			if time < min_time:
				min_time = time
			if time > max_time:
				max_time = time
		
		period = (max_time - min_time).total_seconds()

		documents_send = [{"X": (doc_topic.document.time - min_time).total_seconds() / period, 
						   "Y": doc_topic.topic.spectrum_index,
						   "id": doc_topic.document.id} for doc_topic in doc_topics]
		topics = Topic.objects.filter(model = self, layer = self.layers_count).order_by("spectrum_index")
		topics_send = [{"Y": topic.spectrum_index, "name": topic.title} for topic in topics]
		return "docs=" + json.dumps(documents_send) + ";\ntopics=" + json.dumps(topics_send) + ";\n";
				
				
class Topic(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	id_model = models.IntegerField(null = True)
	title = models.TextField(null=False)
	title_short = models.TextField(null=True) 
	spectrum_index = models.IntegerField(null = True, default = 0) 
	layer = models.IntegerField(default = 1) 
	
	def __str__(self):
		return self.title
		
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

'''
class DocumentInDocument(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	document1 = models.ForeignKey(Document, null = False, related_name = 'fk1')
	document2 = models.ForeignKey(Document, null = False, related_name = 'fk2')
	weight = models.FloatField()
	def __str__(self):
		return str(self.document2) + "{0:.1f}%".format(100 * self.weight)		
'''

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