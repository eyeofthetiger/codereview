from django.conf.urls import patterns, url

from review import views, development, annotator, submission

""" This file contains the URL patterns for the codereview app. """

urlpatterns = patterns('',
    # Index URL
	url(r'^$', views.index, name='index'),

    # Login URLs
    url(r'^choose_user/$', development.choose_user, name='choose_user'),
    url(r'^load_student/$', development.load_student, name='load_student'),
    url(r'^load_admin/$', development.load_admin, name='load_admin'),

    # Settings URLs
    url(r'^settings/$', views.email_preferences, name='email_preferences'),

    # Staff URLs
    url(r'^staff/$', views.staff, name='staff'),
    url(r'^staff/submissions/(?P<assignment_pk>\d+)/$', views.list_submissions, 
        name='list_submissions'),
    url(r'^(?P<assignment_pk>\d+)/edit/$', views.edit_assignment, 
        name='edit_assignment'),
    url(r'^add_assignment/$', views.add_assignment, name='add_assignment'),

    # Assignment URLs
    url(r'^(?P<assignment_pk>\d+)/$', views.assignment, name='assignment'),
    url(r'^(?P<assignment_pk>\d+)/description/$', views.assignment_description, 
        name='assignment_description'),

    # Forum URLs
    url(r'^forum/$', views.forum, name='forum'),
    url(r'^add_question/$', views.add_question, name='add_question'),
    url(r'^edit_question/(?P<question_pk>\d+)/$', views.edit_question, 
        name='edit_question'),
    url(r'^question/(?P<question_pk>\d+)/$', views.question, name='question'),
    url(r'^sticky/(?P<question_pk>\d+)/$', views.sticky, name='sticky'),
    url(r'^set_as_answer/(?P<response_pk>\d+)/$', views.set_as_answer, 
        name='set_as_answer'),

    # Submission URLs
    url(r'^submit/(?P<submission_pk>\d+)/$', views.submit_assignment, 
        name='submit_assignment'),
    url(r'^submission/(?P<submission_pk>\d+)/$', views.submission, 
        name='submission'),
    url(r'^submission/(?P<submission_pk>\d+)/download/$', views.download, 
        name='download'),
    url(r'^get_submission_file/$', submission.get_submission_file, 
        name='get_submission_file'),

    # Annotation API URLs
    url(r'^annotator_api/$', annotator.api_root, name='api_root'),
    url(r'^annotator_api/annotations$', annotator.api_index, name='api_index'),
    url(r'^annotator_api/annotations/(?P<comment_pk>\d+)$', annotator.api_read, 
        name='api_read'),
    url(r'^annotator_api/search$', annotator.api_search, name='api_search'),
    url(r'^annotator_api/delete/(?P<user_pk>\d+)/(?P<submission_file_pk>\d+)$',
        annotator.api_delete_all, name='api_delete_all'),

    # Review URLs
    url(r'^submit_review/(?P<user_pk>\d+)/(?P<submission_pk>\d+)$', 
        annotator.submit_review, name='submit_review'),

    # Development/Testing URLs
    url(r'^reset/$', development.reset_test_database, 
        name='reset_test_database'),

    ######### FOR MAURICIOS INDIVIDUAL PROJECT ########
    url(r'^faq/(?P<faq_pk>\d+)/$', views.faq, name='faq'),
    url(r'^add_faq/$', views.add_faq, name='add_faq'),

)