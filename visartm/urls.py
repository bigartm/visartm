from django.conf.urls import url, include
from django.contrib import admin
 
import visartm.views as general_views
import datasets.views as datasets_views
import visual.views as visual_views
import models.views as models_views



 
urlpatterns = [
    url(r'^admin/', admin.site.urls),
	url('accounts/', include('accounts.urls')),
	url(r'^api/', include('api.urls')), 
	url(r'^assessment/', include('assessment.urls')), 
	url(r'^research/', include('research.urls')),
	url(r'^tools/', include('tools.urls')),
	
	
	# general
	url(r'^$', general_views.start_page, name='home'),
	url(r'^settings', general_views.settings_page),
	
	 
	# Datasets	
	url(r'^datasets/reload$', datasets_views.dataset_reload),
	url(r'^datasets/create$', datasets_views.dataset_create),
	url(r'^datasets/delete$', datasets_views.dataset_delete),
	url(r'^datasets/dump$', datasets_views.dump),
    url(r'^datasets$', datasets_views.datasets_list),
    url(r'^dataset$', datasets_views.visual_dataset),
	url(r'^term$', datasets_views.visual_term),	
	url(r'^modality$', datasets_views.visual_modality),	
	url(r'^search$', datasets_views.global_search),	
	url(r'^document$', datasets_views.visual_document), 
	
	# Visualization
	url(r'^visual/global$', visual_views.visual_global),  
	
	# Models and topics
	url(r'^topic$', models_views.visual_topic),
	url(r'^model$', models_views.visual_model), 
	url(r'^models/reload_model$', models_views.reload_model),
	url(r'^models/arrange_topics$', models_views.arrange_topics),	
	url(r'^models/reset_visuals$', models_views.reset_visuals),	
	url(r'^models/create$', models_views.create_model),
	url(r'^models/delete_model$', models_views.delete_model),
	url(r'^models/delete_all_models$', models_views.delete_all_models),
	url(r'^models/settings$', models_views.model_settings),
	url(r'^topics/rename$', models_views.rename_topic),
]
