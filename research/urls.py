from django.conf.urls import url
import research.views as research_views

urlpatterns = [
    url(r'^$', research_views.researches),
    url(r'^create$', research_views.create_research),
    url(r'^rerun$', research_views.rerun_research),
    url(r'^scripts/(?P<script_name>\w+)$', research_views.view_script),
    url(r'^(?P<research_id>\d+)/$', research_views.show_research),
    url(r'^(?P<research_id>\d+)/pic/(?P<pic_id>\d+).png$',
        research_views.get_picture),
    url(r'^(?P<research_id>\d+)/pic/(?P<pic_id>\w+).eps$',
        research_views.get_picture_eps),
    url(r'^(?P<research_id>\d+)/pic/(?P<txt_id>\d+).txt$',
        research_views.get_txt)
]
