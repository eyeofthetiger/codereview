from django.conf.urls import patterns, url

from review import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
    url(r'^(?P<assignment_pk>\d+)/$', views.assignment, name='assignment'),
    url(r'^(?P<assignment_pk>\d+)/description/$', views.assignment_description, name='assignment_description'),
    url(r'^(?P<assignment_pk>\d+)/submission/$', views.submission, name='submission'),
    url(r'^view/(?P<submission_file_pk>\d+)/$', views.view_file, name='view_file'),
    url(r'^review/(?P<submission_pk>\d+)/$', views.review_submission, name='review_submission'),
    url(r'^get_submission_file/$', views.get_submission_file, name='get_submission_file'),
)