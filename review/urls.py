from django.conf.urls import patterns, url

from review import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
    url(r'^(?P<assignment_id>\d+)/$', views.assignment, name='assignment'),
    url(r'^(?P<assignment_id>\d+)/(?P<submission_id>\d+)/(?P<submission_file_id>\d+)/$', views.view_file, name='view_file'),
)