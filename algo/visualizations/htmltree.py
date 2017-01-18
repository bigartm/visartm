from models.models import Topic, TopicInTopic 

def visual(model, params):
	root_topic = Topic.objects.filter(model = model, layer = 0)[0] 
	topics = TopicInTopic.objects.filter(model = model, parent = root_topic).order_by("child__spectrum_index")
	return "<ul>" + "".join([tree_presentation(topic.child, model) for topic in topics]) + "</ul>"

def tree_presentation(topic, model):
	ret = "<li><a href='/visual/topic?id=" + str(topic.id) + "'>" + topic.title + "</a></li>"
	children = TopicInTopic.objects.filter(model = model, parent = topic).order_by("child__spectrum_index")
	if len(children) > 0:
		ret += "<ul>" + "".join([tree_presentation(topic.child, model) for topic in children]) + "</ul>"
	return ret