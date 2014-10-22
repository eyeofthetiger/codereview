from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

	#Main app urls
    url(r'^$', include('review.urls')),
    url(r'^app/', include('review.urls')),

	#Built in Django Admin url
    url(r'^admin/', include(admin.site.urls)),
)