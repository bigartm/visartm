from django.conf.urls import url
import accounts.views as accounts_views
import django.contrib.auth.views as auth_views

urlpatterns = [
    url(r'^login', accounts_views.login_view),
    url(r'^logout', accounts_views.logout_view),
    url(r'^signup', accounts_views.signup),
    url(r'^sendmail', accounts_views.sendmail),
    url(r'password_reset_done$', auth_views.password_reset_done,
        name='password_reset_done'),
    url(r'password_reset_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'password_reset_complete$', auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'password_reset', auth_views.password_reset, name='password_reset'),
    url(r'^user/(?P<user_name>.+)$',
        accounts_views.account_view,
        name='account'),
    url(r'^group/(?P<group_id>\d+)$', accounts_views.group_view, name='group'),

    url(r'^vk_get_token', accounts_views.vk_get_token),
    url(r'^vk_confirm_token$', accounts_views.vk_confirm_token),
]
