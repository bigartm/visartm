from django.conf.urls import url
import research.views as research_views

urlpatterns = [
	url(r'^create$', research_views.create_research),
	url(r'^rerun$', research_views.rerun_research),
	url(r'^(?P<research_id>\d+)/$', research_views.show_research),
	url(r'^(?P<research_id>\d+)/pic/(?P<pic_id>\d+).png$', research_views.get_picture)	
]