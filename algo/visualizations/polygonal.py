from models.models import Topic 


def visual(model, params):
	root_topic = Topic.objects.filter(model = model, layer = 0)[0]
	return "Not ready"
	
	
def renderTopic(topic, model):
	