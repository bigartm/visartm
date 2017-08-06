from models.models import Topic, TopicInTopic
import json


def visual(vis, params):
    root_topic = Topic.objects.get(model=vis.model, layer=0)
    return json.dumps({"children": build_circles(vis.model, root_topic)})


def build_circles(model, topic):
    answer = []
    if topic.layer == model.layers_count:
        for document in topic.get_documents():
            answer.append({"id": document.id, "size": 1})
    else:
        relations = TopicInTopic.objects.filter(parent=topic)
        for relation in relations:
            child = relation.child
            answer.append(
                {"name": child.title, "children": build_circles(model, child)})
    return answer
