from django.contrib import admin
from review.models import Submission, SubmissionFile, Assignment, Course, \
	AssignedReview, Comment, CommentRange

""" This file is used to register which Models will be represented in Django's 
	built in admin system.
"""

admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(SubmissionFile)
admin.site.register(AssignedReview)
admin.site.register(Comment)
admin.site.register(CommentRange)
