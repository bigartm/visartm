from django.conf.urls import url
import tools.views as tools_views

urlpatterns = [
	url(r'^$', tools_views.tools_list),
	url(r'^vw2uci', tools_views.vw2uci),
	url(r'^uci2vw', tools_views.uci2vw),
	url(r'^vkloader', tools_views.vkloader), 
]