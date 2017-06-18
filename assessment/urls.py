from django.conf.urls import url
import assessment.views as assessment_views

urlpatterns = [
	url(r'^$', assessment_views.problems_list),
	url(r'^problem$', assessment_views.problem),
	url(r'^create_problem$', assessment_views.create_problem),
	url(r'^task$', assessment_views.task),
	url(r'^get_task$', assessment_views.get_task),	
	url(r'^add_assessor$', assessment_views.add_assessor),	
	url(r'^delete_assessor$', assessment_views.delete_assessor),	
	url(r'^get_results$', assessment_views.get_results),
	url(r'^instructions$', assessment_views.instructions),
	url(r'^accept_exam$', assessment_views.accept_exam),
]