from django.contrib import admin
from review.models import Submission, SubmissionFile, Assignment, Course, UserAccount, AssignedReview, Comment, CommentRange

admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(SubmissionFile)
admin.site.register(UserAccount)
admin.site.register(AssignedReview)
admin.site.register(Comment)
admin.site.register(CommentRange)
