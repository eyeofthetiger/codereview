from django.conf.urls import patterns, url

from review import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
    url(r'^(?P<assignment_pk>\d+)/$', views.assignment, name='assignment'),
    url(r'^(?P<assignment_pk>\d+)/description/$', views.assignment_description, name='assignment_description'),
    url(r'^submission/(?P<submission_pk>\d+)/$', views.submission, name='submission'),
    url(r'^get_submission_file/$', views.get_submission_file, name='get_submission_file'),
)