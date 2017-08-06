from django.conf.urls import url
import models.views as models_views

urlpatterns = [
    url(r'^$', models_views.models_list),
    url(r'^reload_model$', models_views.reload_model),
    url(r'^arrange_topics$', models_views.arrange_topics),
    url(r'^reset_visuals$', models_views.reset_visuals),
    url(r'^create$', models_views.create_model),
    url(r'^delete_model$', models_views.delete_model),
    url(r'^delete_all_models$', models_views.delete_all_models),
    url(r'^settings$', models_views.model_settings),
    url(r'^rename_topic$', models_views.rename_topic),
    url(r'^related_topics$', models_views.related_topics),
    url(r'^model_log$', models_views.model_log),
    url(r'^dump$', models_views.dump_model),
    url(r'^delete_cached_distances$', models_views.delete_cached_distances),
]
