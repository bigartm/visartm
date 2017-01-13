from django.shortcuts import render
from datasets.models import Dataset, Document
from django.http import HttpResponse
import json
import os
from django.conf import settings

def _acao_response(response):
	response['Access-Control-Allow-Origin'] = '*'
	response['Access-Control-Allow-Methods'] = 'GET'

def get_documents(request):
	ids = request.GET["ids"].split(',')
	full = "full" in request.GET
	result = []
	for id in ids:
		try:
			document = Document.objects.filter(id = int(id))[0]
			doc = {
				"id": document.id,
				"title": document.title,
				"date": document.time.strftime("%X"),
				"time": document.time.strftime("%x"),
				"url": document.url,
				"snippet": document.snippet,
			}
			
			if full:
				document = Document.objects.filter(id = int(id))[0]
				file_name = os.path.join(settings.DATA_DIR, "datasets", document.dataset.text_id, "documents", str(document.model_id) + ".txt")
				with open(file_name, encoding = "utf-8") as f:
					doc["text"] = f.read()
			
			result.append(doc)
		except:
			pass
			
	response =  HttpResponse(json.dumps(result), content_type='application/json')  
	_acao_response(response)
	return response
	 
	
