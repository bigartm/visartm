from datasets.models import Document
from models.models import Topic, DocumentInTopic
import json 

def visual(model, params): 		 
	documents = Document.objects.filter(dataset = model.dataset)
	doc_topics = DocumentInTopic.objects.filter(model = model)		
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
	topics = Topic.objects.filter(model = model, layer = model.layers_count).order_by("spectrum_index")
	topics_send = [{"Y": topic.spectrum_index, "name": topic.title} for topic in topics]
	return "docs=" + json.dumps(documents_send) + ";\ntopics=" + json.dumps(topics_send) + ";\n";