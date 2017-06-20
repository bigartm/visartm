from models.models import Topic, TopicInTopic 
import json

def visual(vis, params):
	model = vis.model
	topics_count = [int(x) for x in model.topics_count.split()]
	topics = [{
		"id": topic.id, 
		"title": topic.title, 
		"x": topic.layer, 
		"y": (0.5 + topic.spectrum_index) / topics_count[topic.layer]
	} for topic in Topic.objects.filter(model = model)]
	links = []
	
	root_topic = Topic.objects.filter(model = model, layer = 0)[0] 
	get_links(root_topic, links, topics_count)
	
	
	return "topics=" + json.dumps(topics) + ";\n" + \
		   "links=" + json.dumps(links) + ";\n" + \
		   "lines_count=%d;\n" % model.get_layer_size(model.layers_count)
		   
def get_links(topic, links, topics_count):
	l = topic.layer
	text_width = len(topic.title)
	for relation in TopicInTopic.objects.filter(parent=topic):
		links.append({
			"x1": l,
			"y1": (0.5 + topic.spectrum_index) / topics_count[l], 
			"y2": (0.5 + relation.child.spectrum_index) / topics_count[l+1],
			"text_width" : text_width
		})
		get_links(relation.child, links, topics_count)
		