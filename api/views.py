from django.shortcuts import render
from datasets.models import Dataset, Document, Modality, Term
from models.models import Topic
from visual.models import Polygon
from django.http import HttpResponse
import json
import os
import struct
from django.conf import settings
#from django.core.paginator import Paginator


def allow(func):
	def wrapped(request):
		response = func(request)
		response['Access-Control-Allow-Origin'] = '*'
		response['Access-Control-Allow-Methods'] = 'GET'
		return response
	return wrapped
	
	
@allow
def get_documents(request):
	result = []
		
	offset = 0 
	if 'offset' in request.GET:
		offset = int(request.GET["offset"])	
	count = 100 
	if 'count' in request.GET:
		count = int(request.GET["count"])
	if 'fields' in request.GET:
		fields = request.GET["fields"].split(',')	
	else:
		fields = {}
		
		
	if 'ids' in request.GET:
		ids = request.GET["ids"].split(',')
		documents = Document.objects.filter(id__in = ids)
		for document in documents: 
			doc = {
				"id": document.id,
				"title": document.title,
				"url": document.url,
				"snippet": document.snippet,
			}
			time = document.time
			if not time is None:
				doc["date"] = time.strftime("%x");
				doc["time"] = time.strftime("%X")
			if "text" in fields:
				doc["text"] = document.get_text()
			result.append(doc)
	elif 'topic_id' in request.GET:
		topic = Topic.objects.get(id = request.GET["topic_id"])
		if offset + count > topic.documents_count:
			count = topic.documents_count - offset
		dataset_id = topic.model.dataset.id
		s = topic.documents[8 * offset : 8 * (offset + count)]
		for i in range(count): 
			document = Document.objects.get(dataset_id = dataset_id, index_id = struct.unpack('I', s[8 * i : 8 * i + 4])[0])
			result.append({
				"id": document.id,
				"title": document.title,
				"weight": "{:0.2f}".format(100*(struct.unpack('f', s[8*i+4 : 8*i+8])[0]))
			})	
	elif 'dataset_id' in request.GET: 
		for document in Document.objects.filter(dataset_id = request.GET["dataset_id"]).order_by("index_id")[offset : offset + count]:
			result.append({
				"id": document.id,
				"title": document.title
			})
	elif 'term_id' in request.GET:  
		term = Term.objects.get(id = request.GET["term_id"])
		term.count_documents_index()
		docs_index = term.documents
		length = len(docs_index) // 6
		if offset + count > length:
			count = length - offset 
		for i in range(offset, offset + count):
			doc_iid = struct.unpack('I', docs_index[6*i: 6*i+4])[0]
			document = Document.objects.get(dataset_id=term.dataset_id, index_id=doc_iid) 
			result.append({
				"id": document.id,
				"title": document.title,
				"count": struct.unpack('H', docs_index[6*i+4: 6*i+6])[0],
				"concordance": document.get_concordance([term.index_id])
			})			
	return HttpResponse(json.dumps(result), content_type='application/json')  
	 
	 
@allow
def get_polygon_children(request):
	polygon = Polygon.objects.filter(id = request.GET['id'])[0]
	polygon.place_children()
	result = []
	for child in Polygon.objects.filter(parent = polygon):
		result.append(child.to_json_object())
	return HttpResponse(json.dumps(result), content_type='application/json')  

@allow
def set_parameter(request):
	if request.GET['entity'] == 'Modality':
		target = Modality.objects.filter(id = request.GET['id'])[0]
		if request.GET['param'] == 'is_word':
			target.is_word = change_boolean(target.is_word, request.GET['value'])
		elif request.GET['param'] == 'is_tag':
			target.is_tag = change_boolean(target.is_tag, request.GET['value'])
		target.save()
	return HttpResponse("OK")
	
def change_boolean(initial, new):
	if new == "change":
		return not initial
	return (new == 'true')
	
