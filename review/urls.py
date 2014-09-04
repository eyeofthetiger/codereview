from django.conf.urls import patterns, url

from review import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
    url(r'^choose_user/$', views.choose_user, name='choose_user'),
    url(r'^load_student/$', views.load_student, name='load_student'),
    url(r'^load_admin/$', views.load_admin, name='load_admin'),
    url(r'^staff/$', views.staff, name='staff'),
    url(r'^staff/submissions/(?P<assignment_pk>\d+)/$', views.list_submissions, name='list_submissions'),
    url(r'^(?P<assignment_pk>\d+)/$', views.assignment, name='assignment'),
    url(r'^(?P<assignment_pk>\d+)/description/$', views.assignment_description, name='assignment_description'),
    url(r'^submit/(?P<submission_pk>\d+)/$', views.submit_assignment, name='submit_assignment'),
    url(r'^submission/(?P<submission_pk>\d+)/$', views.submission, name='submission'),
    url(r'^get_submission_file/$', views.get_submission_file, name='get_submission_file'),
    url(r'^annotator_api/$', views.api_root, name='api_root'),
    url(r'^annotator_api/annotations$', views.api_index, name='api_index'),
    url(r'^annotator_api/annotations/(?P<comment_pk>\d+)$', views.api_read, name='api_read'),
    url(r'^annotator_api/search$', views.api_search, name='api_search'),
    url(r'^reset/$', views.reset_test_database, name='reset_test_database'),
)