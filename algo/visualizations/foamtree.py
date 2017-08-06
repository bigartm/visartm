from models.models import Topic, TopicInTopic
import json


def visual(vis, params):
    root_topic = Topic.objects.get(model=vis.model, layer=0)
    if len(params) > 1 and params[1] == "light":
        groups = build_foamtree_light(vis.model, root_topic)
    else:
        groups = build_foamtree(vis.model, root_topic)
    return json.dumps({"groups": groups, "label": vis.model.dataset.name})


def build_foamtree(model, topic):
    answer = []
    if topic.layer == model.layers_count:
        for document in topic.get_documents():
            answer.append({"label": document.title, "id": document.id})
    else:
        relations = TopicInTopic.objects.filter(parent=topic)
        for relation in relations:
            child = relation.child
            answer.append(
                {"label": child.title, "groups": build_foamtree(model, child)})
    return answer


def build_foamtree_light(model, topic):
    answer = []
    if topic.layer != model.layers_count:
        relations = TopicInTopic.objects.filter(parent=topic)
        for relation in relations:
            child = relation.child
            answer.append({
                "label": child.title,
                "groups": build_foamtree_light(model, child)})
    return answer
