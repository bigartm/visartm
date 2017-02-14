from django.conf.urls import url, include
from django.contrib import admin
 
import visartm.views as general_views
import datasets.views as datasets_views
import visual.views as visual_views
import models.views as models_views
import api.views as api_views
import assessment.views as assessment_views
import research.views as research_views

 
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
	url('accounts/', include('accounts.urls')),
 
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
	
	# Documents
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
	url(r'^topics/rename$', models_views.rename_topic),
	
	# API
	url(r'^api/documents/get$', api_views.get_documents),
	url(r'^api/polygons/children$', api_views.get_polygon_children),
	url(r'^api/settings/set$', api_views.set_parameter),
	
	# Assessment
	url(r'^assessment/problem$', assessment_views.problem),
	url(r'^assessment/task$', assessment_views.task),
	url(r'^assessment/get_task$', assessment_views.get_task),	
	url(r'^assessment/add_assessor$', assessment_views.add_assessor),	
	url(r'^assessment/delete_assessor$', assessment_views.delete_assessor),	
	url(r'^assessment/get_results$', assessment_views.get_results),
	url(r'^assessment/instructions$', assessment_views.instructions),
	
	# Research
	url(r'^research/create$', research_views.create_research),
	url(r'^research/rerun$', research_views.rerun_research),
	url(r'^research/(?P<research_id>\d+)/$', research_views.show_research),
	url(r'^research/(?P<research_id>\d+)/pic/(?P<pic_id>\d+).png$', research_views.get_picture)	
]
