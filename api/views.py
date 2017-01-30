from django.shortcuts import render
from datasets.models import Dataset, Document, Modality, Term, TermInDocument
from models.models import DocumentInTopic
from visual.models import Polygon
from django.http import HttpResponse
import json
import os
from django.conf import settings
#from django.core.paginator import Paginator

def _acao_response(response):
	response['Access-Control-Allow-Origin'] = '*'
	response['Access-Control-Allow-Methods'] = 'GET'

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
				doc["text"] = documnt.get_text()
			result.append(doc)
	elif 'topic_id' in request.GET:
		print("O,C" ,offset, count)
		topic_id = request.GET["topic_id"]
		relations = DocumentInTopic.objects.filter(topic_id = topic_id).order_by("-weight")
		
		relations = relations[offset : offset + count]
		#if offset % count != 0:
		#	raise ValueError("Invalif page")
		#relations = Paginator(relations, count).page(offset // count + 1)
		
		
		for relation in relations: 
			doc = {
				"id": relation.document.id,
				"title": relation.document.title,
				"weight": "{:0.2f}".format(100*relation.weight)
			}
			result.append(doc)
	elif 'term_id' in request.GET:
		print("O,C" ,offset, count)
		term = Term.objects.filter(id = request.GET["term_id"])[0]
		relations = TermInDocument.objects.filter(term = term).order_by("-count")
		relations = relations[offset : offset + count]
		for relation in relations: 
			doc = {
				"id": relation.document.id,
				"title": relation.document.title,
				"count": relation.count,
				"concordance": relation.document.get_concordance(term)
			}
			result.append(doc)
			
	response =  HttpResponse(json.dumps(result), content_type='application/json')  
	_acao_response(response)
	return response
	 
def get_polygon_children(request):
	print("API for" + request.GET['id'])
	polygon = Polygon.objects.filter(id = request.GET['id'])[0]
	polygon.place_children()
	result = []
	for child in Polygon.objects.filter(parent = polygon):
		result.append(child.to_json_object())
	response =  HttpResponse(json.dumps(result), content_type='application/json')  
	_acao_response(response)
	return response
	
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
	
