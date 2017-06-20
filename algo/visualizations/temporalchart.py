from models.models import Topic, TopicInTopic
import json

def visual(vis, params): 
	model = vis.model		
	group_by = params[1]		# year,month,week,day
	topics = Topic.objects.filter(model = model, layer = model.layers_count).order_by("spectrum_index")	
	topics = [topic.title for topic in topics]
	cells, dates = model.group_matrix(group_by=group_by, named_groups=False)
	 
	topics_count = len(topics)
	dates_count = len(dates)
	charts = [[topics[y]] + [len(cells[x][y]) for x in range(dates_count)] for y in range(topics_count)]
	
	dates = [str(date.date()) for date in dates]
	
	return  "charts=" + json.dumps(charts) + ";\n" + \
			"dates=" + json.dumps(['date'] + dates) + ";\n";
