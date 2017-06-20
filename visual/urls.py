from django.conf.urls import url
import visual.views as visual_views 

urlpatterns = [
	url(r'^global', visual_views.visual_global),
	url(r'^example/(?P<vis_name>\w+)$', visual_views.example),
	url(r'^clear', visual_views.clear),
]