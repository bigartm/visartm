from models.models import Topic, TopicInTopic 

def visual(vis, params):
	topics = Topic.objects.filter(model=vis.model, layer=vis.model.layers_count).order_by("spectrum_index")
	return "<br>".join([topic.top_words_list(count=10) for topic in topics])