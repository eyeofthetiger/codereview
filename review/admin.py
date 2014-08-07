from django.contrib import admin
from review.models import Submission, SubmissionFile, Assignment, Course

admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(SubmissionFile)