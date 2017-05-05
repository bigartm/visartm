from django.db import models
from datasets.models import Dataset, Term, Document, Modality
from django.contrib.auth.models import User
from datetime import datetime
import os
from django.conf import settings
import json
import numpy as np
import pandas as pd 
import artm
import re
from shutil import rmtree 
from django.db import transaction
import traceback
import struct
import time
import algo.metrics as metrics

from models.bigartm_config import BANNED_WORDS


class ArtmModel(models.Model):
	dataset = models.ForeignKey(Dataset, null = False)
	creation_time = models.DateTimeField(null=False, default = datetime.now)
	text_id = models.TextField(null=False, default = "")
	#main_modality = models.ForeignKey(Modality, null = True)
	name = models.TextField(null=True)
	author = models.ForeignKey(User, null=True)
	layers_count = models.IntegerField(default = 1) 
	topics_count = models.TextField(null = False, default = "")
	status = models.IntegerField(null = False, default = 0)  #0-ready,  1-running, 2-error, 3-empty, 11-running, but not critical
	error_message = models.TextField(null=True, blank=True) 
	arrangement_mode = models.TextField(default="none", null=False) 
	metric = models.TextField(default="jaccard", null=False) 
	threshold_hier = models.IntegerField(null = False, default = 100) 
	threshold_docs = models.IntegerField(null = False, default = 100) 
	max_parents_hier = models.IntegerField(null = False, default = 1) 
	topic_naming_top_words = models.IntegerField(null = False, default = 3) 
	
	
	def __str__(self):
		if not self.name or len(self.name) == 0:
			return self.text_id
		else: 
			return self.name	
	
	def get_model(request, modify=False):
		if "model_id" in request.GET:
			model = ArtmModel.objects.get(id=request.GET['model_id'])
		else:
			return None
		
		if not model.dataset.is_public and model.dataset.owner != request.user:
			return None
		
		if not modify and not model.author == request.user:
			return None
			
		return model
	
	def create_generic(self, POST):
		mode = POST['mode']
		self.text_id = "model_" + str(self.id) 
		
		
		try:
			if mode == 'flat': 
				self.prepare_log("Creating flat model (auto)")
				iter_count = int(POST.getlist('iter_count')[0])
				self.layers_count = 1
				self.topics_count = "1 " + POST.getlist('num_topics')[0]
				self.save()
				
				regularizers = {}
				if "regularizers" in POST:
					regularizers = json.loads(POST["regularizers"])
				artm_object = self.create_simple(iter_count = iter_count, regularizers=regularizers)
				self.save_matrices(artm_object)
			elif mode == "hier":
				self.prepare_log("Creating hierarchical model (auto)")
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
				self.prepare_log("Running custom sript...")		
				exec(code, local_vars)
				self.log("Custom script finished.")
				artm_object = local_vars["model"]
				self.save_matrices(artm_object)
			elif mode == "custom":
				raise Exception("You cannot upload scripts.")
			elif mode == "matrices":
				self.text_id = POST["matrices_folder"]
				self.prepare_log("Model will be loaded from matrices")
			elif mode == "empty":
				sample_script_file = os.path.join(self.get_folder(), "sample.py")
				batches_folder = os.path.join(self.dataset.get_folder(), "batches")
				dictionary_file = os.path.join(batches_folder, "dictionary.txt")
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
	
	def create_simple(self, iter_count, regularizers = {}):
		self.log("Creating simple model...")
		layers_count = self.layers_count 
		num_topics = [int(x) for x in self.topics_count.split()]
		
		batch_vectorizer, dictionary = self.dataset.get_batches()
		
		model = artm.hARTM(num_document_passes = iter_count, theta_columns_naming="id")
		model.cache_theta = True
		layers = [0 for i in range(layers_count)]

		layers[0] = model.add_level(num_topics = num_topics[1],
                            topic_names=["topic" + str(t) for t in range(num_topics[1])]
							)
		layers[0].initialize(dictionary=dictionary)
		self.log("Layer 0 initialized.")
		
		
		if (regularizers):
			reg_code = ""
			for name, params in regularizers.items():
				params_init = []
				for pname, value in params.items():
					if len(value)>10:
						raise RuntimeError("Too long value for parameter %s.%s" % (name, pname) )
					params_init.append(pname + "=" + value)
				reg_code += "layers[0].regularizers.add(artm.%s(%s))\n" % (name, ", ".join(params_init))
			self.log("Regularizers to be applied:<br>" + reg_code.replace("\n","<br>"))
			exec(reg_code)
			
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
		 
		if self.dataset.modalities_count > 1:
			for modality in Modality.objects.filter(dataset=self.dataset):
				artm_object.get_phi(class_ids=[modality.name]).to_pickle(os.path.join(self.get_folder(), "phi_" + modality.name))
		 
		is_hierarchial = True
		try:
			layers = artm_object._levels
		except:
			is_hierarchial = False
		
		if is_hierarchial and len(layers) == 1:
			is_hierarchial = False
		
		if is_hierarchial: 
			self.log("Saving matrices psi...")
			for layer_id in range(1, self.layers_count): 
				psi = layers[layer_id].get_psi().to_pickle(os.path.join(self.get_folder(), "psi" + str(layer_id)))
		 
	def gather_phi(self):
		self.log("Loading matrix phi...")
		phi_path = os.path.join(self.get_folder(), "phi")
		phi = None
		topics_count = 0
		if os.path.exists(phi_path):
			phi_raw = pd.read_pickle(os.path.join(self.get_folder(), "phi"))
			if self.dataset.check_terms_order(phi_raw.index):
				phi = phi_raw.values
				self.log("Matrix phi has correct index")
			else:
				self.log("WARNING! Matrix phi has wrong index. Will restore. In case of equal terms in different modalitites there will be errors.")
				topics_count = phi_raw.shape[1]
				phi = np.zeros((self.dataset.terms_count, topics_count))
				self.log("Building terms index...")
				terms_index = self.dataset.get_terms_index()
				self.log("Terms index built.")
				
				ctr = 0
				for row in phi_raw.iterrows():
					term_text = row[0]
					try:
						term_matrix_id = terms_index[term_text]
					except:
						try:
							self.log("WARNING! Word " + term_text + " don't belong to dataset dictionary.")
						except:
							self.log("WARNING! Word (coludn't show) don't belong to dataset dictionary.")
						continue
					for j in range(topics_count):
						phi[term_matrix_id][j] = row[1][j]
					
					if ctr % 10000 == 0:
						self.log(str(ctr))
					ctr += 1
		else:
			self.log("WARNING! Phi wasn't detected. Will try load from matrices for modalities.")
			for modality in Modality.objects.filter(dataset=self.dataset):
				phi_path = os.path.join(self.get_folder(), "phi_" +  modality.name)
				if os.path.exists(phi_path):
					self.log("Found matrix phi for modality " + modality.name + ". Will load.")
					phi_raw = pd.read_pickle(phi_path)
					terms_index = self.dataset.get_terms_index(modality=modality)
					if phi is None:
						topics_count = phi_raw.shape[1]
						phi = np.zeros((self.dataset.terms_count, topics_count))
					if phi_raw.shape[1] != topics_count:
						raise ValueError("Fatal error. Matrices phi are of different width.")
					for row in phi_raw.iterrows():
						term_text = row[0]
						if term_text in terms_index:
							term_matrix_id = terms_index[term_text]
						else:
							self.log("WARNING! Word " + term_text + " don't belong to dataset dictionary.")
							continue
						for j in range(topics_count):
							phi[term_matrix_id][j] = row[1][j]
				else:
					self.log("Fatal error. Matrix for modality " + modality.name + " wasn't found.")
		
		if phi is None:
			raise ValueError("No phi matrix")
		
		self.log("Matrix phi loaded.")
		 
		
		np.save(os.path.join(self.get_folder(), "phi.npy"), phi)
		self.log("Matrix phi saved in numpy format.")
				
				
	def gather_theta(self):
		self.log("Loading matrix theta...")
		theta_raw = pd.read_pickle(os.path.join(self.get_folder(), "theta"))
		self.theta_index = theta_raw.index
		
				
		if (1 in theta_raw) and theta_raw.shape[1] == self.dataset.documents_count:
			self.log("Theta has correct index.")
			theta = theta_raw.sort_index(axis=1).values
		else:
			self.log("Will load theta column by column.")
			if theta_raw.shape[1] != self.dataset.documents_count:
				self.log("WARNING! Not all documents are present in matrix.")
			topics_count = theta_raw.shape[0]
			theta = np.zeros((topics_count, self.dataset.documents_count))
			for document in Document.objects.filter(dataset=self.dataset):
				if document.index_id in theta_raw:
					column = theta_raw[document.index_id]
				elif document.text_id in theta_raw:
					column = theta_raw[document.text_id]
				else:
					self.log("WARNING! Document " + document.text_id + " wasn't found in matrix theta.")
					continue
					
				doc_matrix_id = document.index_id
				for i in range(topics_count):
					theta[i][doc_matrix_id] = column[i]
						 
		
		self.log("Checking matrix theta...")		
		ones = np.sum(theta, axis=0)
		if (np.max(ones) > 1 + 1e3 or np.min(ones) < 1 - 1e3):
			self.log(str(ones))
			raise ValueError("Fuck! Not stochastic!")
		
		self.log("Saving matrix theta...")		
		np.save(os.path.join(self.get_folder(), "theta.npy"), theta)	
		self.log("Matrix theta saved...")	
		
		self.log("Counting topics probabilities using matrix theta")
		pt = np.sum(theta, axis=1) / self.dataset.documents_count
		np.save(os.path.join(self.get_folder(), "pt.npy"), pt)	
		
		
	# Get probabilities of topics on certain layer
	def get_pt(self, layer=1):
		if layer == 0:
			return np.array([1])
		path = os.path.join(self.get_folder(), "pt.npy")
		if not os.path.exists(path):
			self.gather_theta()
		pt = np.load(path)
		ret = pt[self.get_layer_range(layer)]
		self.log("p(t): " + str(ret))
		return ret
		
	@transaction.atomic
	def build_hier(self):
		self.log("Building topics hierarchy")
		threshold_hier = self.threshold_hier / 100.0
		TopicInTopic.objects.filter(model = self).delete()
		topics_count = [int(x) for x in self.topics_count.split()]
		self.build_topics_index()
		
		# Adding topics of top layer as children of root
		for topic_id in self.topics_index[1]:
			relation = TopicInTopic()
			relation.model = self
			relation.parent_id = self.topics_index[0][0]
			relation.child_id = topic_id
			relation.save()		
		
		pt = [self.get_pt(layer=layer) for layer in range(self.layers_count+1)]
			
			
		for bottom_layer in range (2, self.layers_count + 1):
			top_layer = bottom_layer - 1
			psi = self.get_psi(top_layer)
			self.log("Building topics hierarchy between layers %d and %d" % (top_layer, bottom_layer))
			for bottom_topic_id in range(topics_count[bottom_layer]):
				#p = (psi[bottom_topic_id] * pt[top_layer])/pt[bottom_layer][bottom_topic_id] # Conditional probabilities(parent_topic | child_topic)
				p = psi[bottom_topic_id]
				best_top_topic_id = np.argmax(p)
				relation = TopicInTopic()
				relation.model = self
				relation.parent_id = self.topics_index[top_layer][best_top_topic_id]
				relation.child_id = self.topics_index[bottom_layer][bottom_topic_id]
				relation.weight = p[best_top_topic_id]
				relation.is_main = True
				relation.save()
				
				if threshold_hier <= 0.5 and self.max_parents_hier > 1:
					pot_parents = np.argsort(p)[-self.max_parents_hier:]
					for top_topic_id in np.argsort(p)[-self.max_parents_hier:]:
						if p[top_topic_id] > threshold_hier and top_topic_id != best_top_topic_id:
							relation = TopicInTopic()
							relation.model = self
							relation.parent_id = self.topics_index[top_layer][top_topic_id]
							relation.child_id = self.topics_index[bottom_layer][bottom_topic_id]
							relation.weight = p[top_topic_id]
							relation.is_main = False
							relation.save()
			
		
	def extract_docs(self, layer=-1):
		if layer == -1:
			for i in range(1, self.layers_count + 1):
				self.extract_docs(layer=i)
			return
			
		self.log("Extracting documents in topics for layer %d..." % layer)
		threshold_docs = self.threshold_docs / 100.0
		topics_count = [int(x) for x in self.topics_count.split()]
		total_topics_count = sum(topics_count)-1
		theta_t = self.get_theta().transpose()[:, self.get_layer_range(layer)]
		document_bags = [[] for i in range(topics_count[self.layers_count])]	
		for doc_index_id in range(0, self.dataset.documents_count):
			#doc_id = documents_index[doc_index_id].id 
			distr = theta_t[doc_index_id]
			best_topic_id = distr.argmax()
			
			document_bags[best_topic_id].append((distr[best_topic_id], doc_index_id))
			# self.log("Document " +  str(doc_index_id) + " appended to topic " + str(best_topic_id))
			if threshold_docs <= 0.5:
				for topic_id in range(topics_count[self.layers_count]):
					if distr[topic_id] > threshold_docs and topic_id != best_topic_id:
						document_bags[topic_id].append(distr[topic_id], doc_index_id)
			
			if doc_index_id % 1000 == 0:
				self.log(str(doc_index_id)) 
		
		
		self.log("Building topics index...")
		
		
		self.log("Saving topics...") 
		for topic in Topic.objects.filter(model=self, layer=layer).order_by("index_id"): 
			topic.documents = bytes()
			document_bags[topic.index_id].sort(reverse = True)
			for weight, doc_index_id in document_bags[topic.index_id]:
				topic.documents += struct.pack('I', doc_index_id) + struct.pack('f', weight) 
			topic.documents_count = len(topic.documents) // 8
			topic.save()	
		
	def build_topics_index(self):
		self.topics_index = [0 for i in range(self.layers_count + 1)]
		
		for layer_id in range(0, self.layers_count + 1):
			self.topics_index[layer_id] = [topic.id for topic in Topic.objects.filter(model=self, layer=layer_id).order_by("index_id")]
				
	@transaction.atomic
	def reload(self):  
		vocab_file = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "UCI", "vocab." + self.dataset.text_id + ".txt")
		self.prepare_log()
		self.log("Reloading model " + str(self.id) + "...")
		
		rmtree(self.get_visual_folder())
		rmtree(self.get_dist_folder())
		
		
		# Loading matrices
		self.gather_phi()
		phi = self.get_phi()
		phi_t = phi.transpose()
		
		self.gather_theta()
		theta = self.get_theta()
		
		self.layers_count = 1
		psi = [0]
		for i in range(1, 100):
			path = os.path.join(self.get_folder(), "psi" + str(i))
			if os.path.exists(path):
				self.log("Loading matrix psi" + str(i))
				psi.append(pd.read_pickle(path).values)
				np.save(os.path.join(path + ".npy"), psi[i])
				self.layers_count = i + 1
			else: 
				break
				
		self.log("Counting topics...")			
		if self.layers_count == 1: 
			self.topics_count = "1 "  + str(theta.shape[0])
		else:		
			self.topics_count = "1 " + str(psi[1].shape[1])
			for layer_id in range(1, self.layers_count):  
				self.topics_count += " " + str(psi[layer_id].shape[0])
		self.log("Topics number: " + self.topics_count)
		
		terms_count = self.dataset.terms_count
		documents_count = self.dataset.documents_count		
		topics_count = [int(x) for x in self.topics_count.split()]
		total_topics_count = sum(topics_count)-1
		
		# Extracting topic names from theta index
		topic_names = [[] for i in range(self.layers_count + 1)]
		offset = 0
		for layer_id in range(1, self.layers_count + 1):
			topic_names[layer_id] = self.theta_index[offset : offset + topics_count[layer_id]]
			offset += topics_count[layer_id]
		
		# Building temporary index for terms
		self.log("Building temporary index for words...")
		terms_index = Term.objects.filter(dataset = self.dataset).order_by("index_id") 
		terms_id_index = [term.id for term in terms_index]
		
		# Removing existing topics and related objects
		from visual.models import GlobalVisualization
		Topic.objects.filter(model = self).delete() 
		
		GlobalVisualization.objects.filter(model = self).delete()
		
		
		
		# Creating topics, loading top terms, topic labeling
		self.log("Creating topics...")
		
		
		# Creating root topic
		root_topic = Topic()
		root_topic.model = self
		root_topic.index_id = 0
		root_topic.title = "root"
		root_topic.layer = 0
		root_topic.save()		 	
		 
		top_terms_size = 100
		
		banned_words = set(BANNED_WORDS)
		title_size = self.topic_naming_top_words
		terms_weights = self.dataset.get_terms_weights("naming") 
		
		
		row_counter = 0
		for layer_id in range(1, self.layers_count + 1):
			for topic_id in range(topics_count[layer_id]):
				topic = Topic()
				topic.model = self
				topic.index_id = topic_id
				topic.layer = layer_id
				topic.matrix_id = row_counter
				topic.save()
				
				# Naming and top words extracting
				distr = phi_t[row_counter] 
				idx = np.argsort(distr)
				idx = idx[::-1]
				mc = self.dataset.modalities_count
				top_terms_counter = dict()
				
				for i in idx:
					weight = distr[i]
					if weight == 0:
						break
					term = terms_index[int(i)]
					mid = term.modality_id
					if not mid in top_terms_counter:
						top_terms_counter[mid] = 0
					if top_terms_counter[mid] < top_terms_size:
						relation = TopTerm()
						relation.topic = topic
						relation.term = term
						relation.weight = weight
						relation.weight_normed = weight * terms_weights[i]
						relation.save()
						
						top_terms_counter[mid] += 1
						if top_terms_counter[mid] == top_terms_size:
							mc -= 1
						if mc == 0:
							break
						 
						
				if 'topic' in topic_names[layer_id][topic_id]:
					terms_to_title = []				
					title_counter = 0	
					idx = np.argsort(phi_t[row_counter] * terms_weights)
					idx = idx[::-1]
					for i in idx:
						term = terms_index[int(i)]
						if title_counter < title_size and not term.text in banned_words:
							title_counter += 1 						
							terms_to_title.append(term.text) 
						else:
							break
					topic.title = ', '.join(terms_to_title)
					topic.title_multiline = '\n'.join(terms_to_title)
				else:
					topic.title = topic_names[layer_id][topic_id]
					topic.title_multiline = '\n'.join(topic.title.split())
					
				topic.title_short = topic.title[0:20]			
				topic.save() 
				 
					
				row_counter += 1
				if row_counter % 10 == 0:
					self.log("Created topic %d/%d." % (row_counter, total_topics_count))
					 
		self.build_hier()
		
			
		# Loading temporary reference for documents
		# documents_index = Document.objects.filter(dataset = self.dataset).order_by("index_id")
		self.extract_docs()
		
		
		
		
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
			
	def prepare_log(self, string=""):
		if len(self.text_id) == 0:
			self.text_id = "model_" + str(self.id)
		self.log_file_name = os.path.join(self.get_folder(), "log.txt")
		with open(self.log_file_name, "w") as f:
			f.write("%s<br>\n" % string)
		self.save()
			
	def log(self, string):
		if settings.DEBUG:
			print(string)
		if settings.THREADING:
			try: 
				with open(self.log_file_name, "a") as f:
					f.write(string + "<br>\n")
			except:
				pass
		
	def read_log(self):
		try:
			with open(os.path.join(self.get_folder(), "log.txt"), "r") as f:
				return f.read()
		except:
			return "Model is being processed..."
	
	
	def get_topics(self, layer=-1):
		if layer == -1:
			layer=self.layers_count
		return Topic.objects.filter(model = self, layer = layer).order_by("index_id")
	
	def get_related_topics(self, topic, metric="default"):
		metric = metrics.get_metric_by_name(metric)
		topics_index = Topic.objects.filter(model=self, layer=topic.layer).order_by("index_id")
	
		phi_t = self.get_phi_t_norm(topic.layer)
		target_row =  phi_t[topic.index_id]
		distances = [metric(target_row, row) for row in phi_t]
		idx = np.argsort(distances)
		return [{"distance":distances[int(i)], "topic": topics_index[int(i)]} for i in idx]
	
	def get_layer_range(self, layer):
		topics_count = [int(x) for x in self.topics_count.split()]
		shift = 0
		for i in range (1, layer):
			shift += topics_count[i]
		return range(shift, shift + topics_count[layer])
		
	def get_topics_distances(self, metric="default", layer=-1):
		if layer == -1:
			layer=self.layers_count
		if layer == 0:
			return np.zeros((1,1))
		
		matrix_name = os.path.join(self.get_dist_folder(), metric + "_" + str(layer) + ".npy")
		try:
			ret = np.load(matrix_name)
		except:
			topics_count = [int(x) for x in self.topics_count.split()]
			ret = np.zeros((topics_count[layer], topics_count[layer]))
			
				
			phi_t = self.get_phi_t_norm(layer)
			
			metric = metrics.get_metric_by_name(metric)
				
			for i in range(topics_count[layer]):
				for j in range(topics_count[layer]):
					ret[i][j] = metric(phi_t[i], phi_t[j])
			np.save(matrix_name, ret)
		return ret
	
	def delete_cached_distances(self):
		rmtree(self.get_dist_folder())
		if hasattr(self, "phi_t_norm"):
			del self.phi_t_norm
	
	# Only horizontal arranging
	@transaction.atomic
	def arrange_topics(self, mode = "default", metric="default", beta=0.8):
		# Counting horizontal relations topic-topic
		self.log("Counting horizontal relations topic-topic...")	 
		self.topics_index = [[topic for topic in Topic.objects.filter(model = self, layer = i).order_by("index_id")] 
			for i in range(self.layers_count + 1)]
		
		if metric == "default":
			metric = metrics.default_metric
		
		TopicRelated.objects.filter(model = self).delete()
		self.topic_distances = [self.get_topics_distances(metric=metric, layer=i) for i in range(self.layers_count + 1)]
		
		for layer_id in range (1, self.layers_count + 1): 
			layer_size = self.get_layer_size(layer_id)
			for i in range(layer_size):
				idx = np.argsort(self.topic_distances[layer_id][i])
				for j in idx[1 : 1 + min(10, layer_size - 1)]:
					relation = TopicRelated()
					relation.model = self
					relation.topic1 = self.topics_index[layer_id][i]
					relation.topic2 = self.topics_index[layer_id][j]
					relation.weight = self.topic_distances[layer_id][i][j]
					relation.save()
		
		topic_hier_relations = TopicInTopic.objects.filter(model=self)
		
		cluster_mode = False
		
		if mode == "default":
			if self.layers_count == 1:
				mode = "hamilton"
			else:
				mode = "hierarchical"
		
		if mode == "hierarchical":
			self.arrange_topics_hierarchical(beta=beta)
		else:
			# Building topics spectrum
			for layer_id in range (1, self.layers_count + 1):
				layer_size = self.get_layer_size(layer_id)
				if cluster_mode:
					if layer_id > 1:
						clusters = []
						init_perm = []
						for i in idx:
							parent_topic = Topic.objects.get(model=self, layer=layer_id-1, index_id=i)
							relations = topic_hier_relations.filter(parent=parent_topic, is_main=True)
							topics = [relation.child.index_id for relation in relations]
							clusters.append(len(topics))
							init_perm += topics
					else:
						init_perm = None
						clusters = None
				
				
				self.log("Building topics spectrum for layer %d, mode=%s, metric=%s..." % (layer_id, mode, metric))
				if mode == "alphabet":
					titles = [self.topics_index[layer_id][topic_id].title for topic_id in range(0, layer_size)]
					idx = np.argsort(titles)
				else:
					from algo.arranging.base import get_arrangement_permutation
					if cluster_mode:
						idx = get_arrangement_permutation(self.topic_distances[layer_id], mode, model=self, clusters=clusters, init_perm=init_perm)
					else:
						idx = get_arrangement_permutation(self.topic_distances[layer_id], mode, model=self)
				
				for i in range(self.get_layer_size(layer_id)):
					topic = self.topics_index[layer_id][idx[i]]
					topic.spectrum_index = i
					topic.save() 
				
		self.status = 0
		self.arrangement_mode = mode
		self.metric = metric
		self.save()
		
		self.log("Resetting visualizations...")
		self.reset_visuals()
	 
	
	def arrange_topics_hierarchical(self, beta=0.8, cross_min_mode="auto"):
		if self.layers_count == 1:
			raise ValueError("Model is flat!")
			
		# Arrange lower level, minimizing NDS
		lower_layer = self.layers_count
		dist = self.topic_distances[lower_layer]
		
		# Correcting matrix
		
		high_topics = Topic.objects.filter(model=self, layer=lower_layer-1)
		pairs = set()
		for topic in high_topics:
			close_topics = [t.child.index_id for t in TopicInTopic.objects.filter(parent=topic)]
			for i in close_topics:
				for j in close_topics:
					pairs.add((i,j))
		
		for i,j in pairs:
			dist[i][j] *= beta
					
		# Arranging lower level
		from algo.arranging.base import get_arrangement_permutation
		idx = get_arrangement_permutation(dist, mode="hamilton", model=self)
		
		for i in range(self.get_layer_size(lower_layer)):
			topic = self.topics_index[lower_layer][idx[i]]
			topic.spectrum_index = i
			topic.save() 
			
		# Arranging higher layers, using mass center principle
		from algo.arranging.crossmin import CrossMinimizer 
		for top_layer_id in range(self.layers_count-1, 0, -1):
			N1 = self.get_layer_size(top_layer_id)
			N2 = self.get_layer_size(top_layer_id+1)
			
			A = np.zeros((N1, N2))
			for i in range(N1):
				topic = self.topics_index[top_layer_id][i]
				for rel in TopicInTopic.objects.filter(parent=topic):
					A[i][rel.child.spectrum_index] = 1
			
			cm = CrossMinimizer(A)
			idx = cm.solve(mode=cross_min_mode, model=self)
			
			for i in range(self.get_layer_size(top_layer_id)):
				topic = self.topics_index[top_layer_id][idx[i]]
				topic.spectrum_index = i
				topic.save() 
			
	#layer must be lower level of opair of interest
	def spectrum_crosses_count(self, layer = -1):
		if layer == -1:
			layer = self.layers_count
		
		links = []
		ans = 0
		
		for topic in self.get_topics(layer=layer-1):
			links += [(topic.spectrum_index, rel.child.spectrum_index) for rel in TopicInTopic.objects.filter(parent=topic)]
		
		for link1 in links:
			for link2 in links:
				if link2[0] > link1[0] and link2[1] < link1[1]:
					ans += 1
		return ans
		
	def neighbor_distance_sum(self, metric="default", layer = -1):
		if layer == -1:
			layer = self.layers_count
			
		perm = [t.index_id for t in Topic.objects.filter(model=self, layer=layer).order_by('spectrum_index')]
		dist = self.get_topics_distances(layer=layer, metric=metric)
		
		return sum([dist[perm[i]][perm[i+1]] for i in range(len(perm)-1) ])
		
		
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
		
	def get_dist_folder(self):
		path = os.path.join(settings.DATA_DIR, "datasets", self.dataset.text_id, "models", self.text_id, "dist")
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path			
	

	def get_phi(self):
		return np.load(os.path.join(self.get_folder(), "phi.npy"))
	
	def get_theta(self):
		try:
			return self.theta
		except:
			self.theta = np.load(os.path.join(self.get_folder(), "theta.npy"))
			return self.theta
	
	
	# Return phi transposed and normalized by modalities weights, for distance counting
	def get_phi_t_norm(self, layer):
		if not hasattr(self, "phi_t_norm"):
			self.phi_t_norm = dict()
		if not layer in self.phi_t_norm:
			phi_t_norm = self.get_phi().transpose()[self.get_layer_range(layer)]
			
			if self.dataset.modalities_count > 1:
				self.log("Normalizing phi according to modalitites weights...")
				phi_t_norm = phi_t_norm * self.dataset.get_terms_weights("spectrum")
				self.log("Normalized.")
				sums = np.sum(phi_t_norm, axis = 1)
				if np.min(sums) < 0.999 or np.max(sums) > 1.001:
					raise RuntimeError("Phi is not stochastic!")
				#print(sums)
			self.phi_t_norm[layer] = phi_t_norm
		return self.phi_t_norm[layer]
			
	def get_theta_t(self):
		try:
			return self.theta_t
		except:
			self.theta_t = self.get_theta().transpose()
			return self.theta_t
			
	def get_psi(self, i):
		return np.load(os.path.join(self.get_folder(), "psi" + str(i) + ".npy"))
	
	def lower_topics_count(self):
		return int(self.topics_count.split()[-1])
	
	def get_layer_size(self, layer):
		return int(self.topics_count.split()[layer])
	
	# Groups documents into matrix Dates-Topics, elements are absolute ids of documents
	# (Always by lower level)
	# Topics are ordered in order of spectrum_index
	# Return tuple - matrix, dates
	def group_matrix(self, group_by="day", named_groups=False):
		from algo.utils.date_namer import DateNamer
		#from models.models import Topic
		documents = Document.objects.filter(dataset = self.dataset)
		topics = Topic.objects.filter(model = self, layer = self.layers_count).order_by("spectrum_index")
		topics_count = len(topics)
		dn = DateNamer(group_by=group_by, lang=self.dataset.language)
		
		dates_hashes = set()
		for document in documents:
			dates_hashes.add(dn.date_hash(document.time))
		dates_hashes = list(dates_hashes)
		dates_hashes.sort()
		dates = []
		dates_reverse_index = dict()
		
		dates_count = 0 
		for date_h in dates_hashes:
			dates_reverse_index[date_h] = dates_count
			if named_groups:
				dates.append(dn.date_name(date_h)) 
			else:
				dates.append(dn.hash_date(date_h)) 
			dates_count += 1
			
		cells = [[[] for j in range(topics_count)] for i in range(dates_count)]
		
		
		for topic in topics:
			y = topic.spectrum_index
			for document in topic.get_documents():
				x = dates_reverse_index[dn.date_hash(document.time)]
				cells[x][y].append(document.id)
		
		return cells, dates
	
	
	
	# Returns list of related documents to the document with given index_id (sorted from most related)
	def get_related_documents(self, document_index_id, count=20, metric="euclidean"):
		documents_count = self.dataset.documents_count
		documents_index = Document.objects.filter(dataset = self.dataset).order_by("index_id")
		dist = np.zeros(documents_count)
		theta_t = self.get_theta_t()
		self_distr = theta_t[document_index_id]
		metric = metrics.get_metric_by_name(metric)
		for other_document_id in range(0, documents_count):
			dist[other_document_id] = metric(self_distr, theta_t[other_document_id])
		
		idx = np.argsort(dist)[1 : count+1]		
		return [documents_index[int(i)] for i in idx]

	def segmentation_available(self, document):
		return os.path.exists(os.path.join(self.get_folder(), "segmentation", document.text_id))
		
	def get_segmentation(self, document):
		try:
			with open(os.path.join(self.get_folder(), "segmentation", document.text_id)) as f:
				return json.loads(f.read())["selections"]
		except:
			return None
			
	def reset_visuals(self):
		from visual.models import GlobalVisualization
		GlobalVisualization.objects.filter(model = self).delete()
			
def on_start():
	for model in ArtmModel.objects.filter(status=1):
		model.status = 2
		model.error_message = "Model processing was interrupted."
		model.save()
		
	for model in ArtmModel.objects.filter(status=11):
		model.status = 0
		model.save() 
		
		
from django.db.models.signals import pre_delete
from django.dispatch import receiver
@receiver(pre_delete, sender=ArtmModel, dispatch_uid='artmmodel_delete_signal')
def remove_model_files(sender, instance, using, **kwargs):
	if settings.DEBUG:
		return
	try:
		rmtree(folder)
	except:
		pass

		
class Topic(models.Model):
	model = models.ForeignKey(ArtmModel, null=False)
	index_id = models.IntegerField(null=True)	# in layer
	matrix_id = models.IntegerField(null=True)  # In matrix
	title = models.TextField(null=False)
	title_short = models.TextField(null=True) 
	spectrum_index = models.IntegerField(null = True, default = 0) 
	layer = models.IntegerField(default = 1) 
	documents = models.BinaryField(null=True) #[4 bytes - document.index_id][4 bytes - weight]
	documents_count =  models.IntegerField(null=False, default=0)
	
	def __str__(self):
		return self.title
		
	def rename(self, new_title):
		self.title = new_title
		self.title_short = new_title[0:30]
		self.save()
		
	def get_documents(self): 
		all_documents = Document.objects.filter(dataset = self.model.dataset)
		for i in range(self.documents_count):
			doc_index_id = struct.unpack('I', self.documents[8*i : 8*i+4])[0]
			yield all_documents.get(index_id = doc_index_id) 
		
	def get_documents_index_ids(self):  
		return [struct.unpack('I', self.documents[8*i : 8*i+4])[0] for i in range(self.documents_count)]
		
		
	def top_words_html(self, count=10):
		ret = ""
		tw = self.top_words(count=count)
		i = 0
		for w in tw:
			ret += w + " "
			i += 1
			if i % 3 == 0:
				ret +="<br>"
		return ret 
		
	def top_words_list(self, count=10):
		return ', '.join(self.top_words(count=count))
			
	def top_words(self, count = 10):
		return [x.term.text for x in TopTerm.objects.filter(topic=self).order_by('-weight_normed')[0:count]]
	
			
		
class TopicInDocument(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	document = models.ForeignKey(Document, null = False)
	topic = models.ForeignKey(Topic, null = False)
	probability = models.FloatField(default=0)
	def __str__(self):
		return str(self.topic) + " " + "{0:.1f}%".format(100 * self.probability)
		
class TopicInTopic(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	parent = models.ForeignKey(Topic, null = False, related_name = 'parent')
	child = models.ForeignKey(Topic, null = False, related_name = 'child')
	weight = models.FloatField(default=0)
	is_main =  models.BooleanField(default=True)
	
		
class TopicRelated(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	topic1 = models.ForeignKey(Topic, null = False, related_name = 'fk1')
	topic2 = models.ForeignKey(Topic, null = False, related_name = 'fk2')
	weight = models.FloatField()
	def __str__(self):
		return str(self.topic2) + "{0:.1f}%".format(100 * self.weight)		

		
class TopTerm(models.Model):
	topic = models.ForeignKey(Topic)
	term = models.ForeignKey(Term)
	weight = models.FloatField(default=0)		
	weight_normed = models.FloatField(default=0)		
	

class TopicInTerm(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	topic = models.ForeignKey(Topic, null = False)
	term = models.ForeignKey(Term, null = False)
	weight = models.FloatField()
	def __str__(self):
		return str(self.term) + " " + str(self.topic) + "{0:.1f}%".format(100 * self.weight)		

	
from django.contrib import admin
admin.site.register(ArtmModel)
admin.site.register(Topic)