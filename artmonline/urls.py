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
    url(r'^datasets', datasets_views.datasets_list),
    url(r'^visual/dataset', datasets_views.visual_dataset),
	
	# Visualization
	url(r'^visual/document', visual_views.visual_document),
	url(r'^visual/doc_all_topics', visual_views.visual_document_all_topics),
	url(r'^visual/term', visual_views.visual_term),	 
	url(r'^visual/global', visual_views.visual_global),
	url(r'^visual/temporal_squares', visual_views.visual_temporal_squares),
	url(r'^visual/html_tree', visual_views.html_tree),  
	
	# Models and topics
	url(r'^visual/topic', models_views.visual_topic),
	url(r'^visual/model', models_views.visual_model),
	url(r'^models/reload_model', models_views.reload_model),
	url(r'^models/arrange_topics', models_views.arrange_topics),	
	url(r'^models/reset_visuals', models_views.reset_visuals),	
	url(r'^models/create', models_views.create_model),
	url(r'^models/delete_model', models_views.delete_model),
	url(r'^models/delete_all_models', models_views.delete_all_models),
	url(r'^models/json', models_views.get_model_json),
	
	# API
	url(r'^api/documents', api_views.get_documents),	
]
