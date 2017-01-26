from django.conf.urls import url, include
from django.contrib import admin
 
import artmonline.views as general_views
import datasets.views as datasets_views
import visual.views as visual_views
import models.views as models_views
import accounts.views as accounts_views
import api.views as api_views

 
urlpatterns = [
	#admininstration
    url(r'^admin/', admin.site.urls),
	
	# built-in login system
	#url('^', 'django.contrib.auth.urls'),
	#url(r'^login/$', auth_views.login, name='login'),
    #url(r'^logout/$', auth_views.logout, name='logout'),
	
	# general
	url(r'^$', general_views.start_page),
	url(r'^settings', general_views.settings_page),
	url(r'^help', general_views.help_page),
	
	 
	
	# auth
	url(r'^accounts/login', accounts_views.login_view),
	url(r'^accounts/logout', accounts_views.logout_view),
	url(r'^accounts/signup', accounts_views.signup),
	url(r'^accounts/(?P<user_name>\w+)/$', accounts_views.account_view),
	
	
	# Datasets	
	url(r'^datasets/reload', datasets_views.datasets_reload),
	url(r'^datasets/create', datasets_views.datasets_create),
    url(r'^datasets', datasets_views.datasets_list),
    url(r'^dataset', datasets_views.visual_dataset),
	url(r'^term', datasets_views.visual_term),	
	url(r'^modality', datasets_views.visual_modality),	
	url(r'^search', datasets_views.global_search),	
	
	
	# Visualization
	url(r'^document', visual_views.visual_document),
	url(r'^visual/document', visual_views.visual_document),
	url(r'^visual/doc_all_topics', visual_views.visual_document_all_topics),
	url(r'^visual/global', visual_views.visual_global),  
	
	# Models and topics
	url(r'^visual/topic', models_views.visual_topic),
	url(r'^visual/model', models_views.visual_model),
	url(r'^models/reload_model', models_views.reload_model),
	url(r'^models/arrange_topics', models_views.arrange_topics),	
	url(r'^models/reset_visuals', models_views.reset_visuals),	
	url(r'^models/create', models_views.create_model),
	url(r'^models/delete_model', models_views.delete_model),
	url(r'^models/delete_all_models', models_views.delete_all_models),
	url(r'^topics/rename', models_views.rename_topic),
	
	# API
	url(r'^api/documents/get', api_views.get_documents),
	url(r'^api/polygons/children', api_views.get_polygon_children),
	
]
