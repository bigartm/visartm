from models.models import Topic, DocumentInTopic, TopicInTopic
import json

def visual(model, params):
	print("CIRCLES CALLED")
	root_topic = Topic.objects.filter(model = model, layer = 0)[0]
	return json.dumps({"children": build_circles(model, root_topic)})	
	
def build_circles(model, topic):
	answer = []
	if topic.layer == model.layers_count:
		relations = DocumentInTopic.objects.filter(topic = topic)
		for relation in relations:
			document = relation.document
			answer.append({"id": document.id, "size":1})
	else:
		relations = TopicInTopic.objects.filter(parent = topic)
		for relation in relations:
			child = relation.child
			answer.append({"name": child.title, "children": build_circles(model, child)})
	return answer