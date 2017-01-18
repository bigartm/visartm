from models.models import Topic, DocumentInTopic, TopicInTopic
import json
		
def visual(model, params):
	root_topic = Topic.objects.filter(model = model, layer = 0)[0]
	if len(params) > 1 and params[1] == "light":
		groups = build_foamtree_light(model, root_topic)
	else:
		groups = build_foamtree(model, root_topic)
	return json.dumps({"groups": groups, "label": model.dataset.name})
	
def build_foamtree(model, topic):	
	answer = []
	if topic.layer == model.layers_count:
		relations = DocumentInTopic.objects.filter(topic = topic)
		for relation in relations:
			document = relation.document
			answer.append({"label": document.title, "id": document.id})
	else:
		relations = TopicInTopic.objects.filter(parent = topic)
		for relation in relations:
			child = relation.child
			answer.append({"label": child.title, "groups": build_foamtree(model, child)})
	return answer
	
def build_foamtree_light(model, topic):	
	answer = []
	if topic.layer != model.layers_count:
		relations = TopicInTopic.objects.filter(parent = topic)
		for relation in relations:
			child = relation.child
			answer.append({"label": child.title, "groups": build_foamtree_light(model, child)})
	return answer