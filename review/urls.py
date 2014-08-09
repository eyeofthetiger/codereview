from django.conf.urls import patterns, url

from review import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
    url(r'^(?P<assignment_pk>\d+)/$', views.assignment, name='assignment'),
    url(r'^(?P<assignment_pk>\d+)/description/$', views.assignment_description, name='assignment_description'),
    url(r'^(?P<assignment_pk>\d+)/(?P<submission_pk>\d+)/(?P<submission_file_pk>\d+)/$', views.view_file, name='view_file'),
)