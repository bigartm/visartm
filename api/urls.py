from django.conf.urls import url
import api.views as api_views

urlpatterns = [
    url(r'^documents/get$', api_views.get_documents),
    url(r'^polygons/children$', api_views.get_polygon_children),
    url(r'^settings/set$', api_views.set_parameter),
]
