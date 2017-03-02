from django.conf.urls import url
import datasets.views as datasets_views
urlpatterns = [
	url(r'^$', datasets_views.datasets_list), 
	url(r'^reload$', datasets_views.dataset_reload),
	url(r'^create$', datasets_views.dataset_create),
	url(r'^delete$', datasets_views.dataset_delete),
	url(r'^dump$', datasets_views.dump), 
]