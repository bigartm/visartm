from datasets.models import Document
from models.models import Topic
import json 

def visual(model, params): 		 
	documents = Document.objects.filter(dataset = model.dataset)
	topics = Topic.objects.filter(model = model, layer = model.layers_count).order_by("spectrum_index")
	min_time = documents[0].time
	max_time = min_time
	
	for document in documents:
		time = document.time
		if time < min_time:
			min_time = time
		if time > max_time:
			max_time = time
	
	period = (max_time - min_time).total_seconds()
	
	documents_send = []
	for topic in topics:
		for document in topic.get_documents():
			documents_send.append({
				"X": (document.time - min_time).total_seconds() / period,
				"Y": topic.spectrum_index,
				"id": document.id
			})
	
	topics_send = [{"Y": topic.spectrum_index, "name": topic.title} for topic in topics]
	return "docs=" + json.dumps(documents_send) + ";\ntopics=" + json.dumps(topics_send) + ";\n";