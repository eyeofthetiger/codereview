from django.utils import timezone

from django.contrib.auth.models import User
from django.db import models

class UserAccount(models.Model):
	""" A User of the application. This extends the default Django User class"""
	user = models.OneToOneField(User)
	#Different from Django's User's user_id field
	institution_user_id = models.CharField(max_length=140)
	is_admin = models.BooleanField()

	def __unicode__(self):
		return self.user.first_name + " " + self.user.last_name + " - " + \
		self.institution_user_id

class Course(models.Model):
	""" The course that this application is being used for. """
	course_name = models.CharField(max_length=140)
	course_code = models.CharField(max_length=40)
	course_id = models.CharField(max_length=140) #Unique ID for course
	year = models.IntegerField()
	#CharField is used to account for cases such as 'summer semester'
	semester = models.CharField(max_length=40)
	institution = models.CharField(max_length=140)

	def __unicode__(self):
		return self.course_code + " - " + self.course_name

class Assignment(models.Model):
	""" An assignment created by a course co-ordinator."""
	assignment_id = models.CharField(max_length=140) #Unique ID for assignment
	name = models.CharField(max_length=140)
	create_date = models.DateTimeField()
	modified_date = models.DateTimeField()
	open_date = models.DateTimeField()
	due_date = models.DateTimeField()
	description = models.TextField()
	allow_multiple_uploads = models.BooleanField()
	allow_help_centre = models.BooleanField()
	number_of_peer_reviews = models.IntegerField()
	review_open_date = models.DateTimeField()
	review_due_date = models.DateTimeField()
	weighting = models.IntegerField()
	has_tests = models.BooleanField()
	test_required = models.BooleanField()

	def __unicode__(self):
		return str(self.name)

	def due_date_passed(self):
		""" Returns true if due date has passed, false otherwise. """
		return self.due_date < timezone.now()

	def get_submission(self, user):
		submissions = Submission.objects.filter(user=user, assignment=self, has_been_submitted=True).order_by('-upload_date')
		if len(submissions) > 0:
			return submissions[0]
		return

class Submission(models.Model):
	""" An assignment submitted by a user. """
	user = models.ForeignKey(User)
	assignment = models.ForeignKey(Assignment)
	upload_date = models.DateTimeField()
	upload_path = models.TextField()
	has_been_submitted = models.BooleanField()
	unviewed_reviews = models.IntegerField()

	def __unicode__(self):
		return str(self.id)

class SubmissionFile(models.Model):
	""" A single file within an assignment submission. file_path is relative,
		and will be joined with the upload_path field in Submission.
	"""
	submission = models.ForeignKey(Submission)
	#TextField is used so there are no restrictions on filename size.
	file_path = models.TextField()

	def __unicode__(self):
		return str(self.file_path)

class AssignedReview(models.Model):
	""" A review of an Submission that has been assigned to a User. """
	assigned_user = models.ForeignKey(User)
	assigned_submission = models.ForeignKey(Submission)
	has_been_reviewed = models.BooleanField()

	def __unicode__(self):
		return str(self.assigned_user) + " to review " + \
		str(self.assigned_submission)

class Comment(models.Model):
	""" A Commment made by a User on a particular SubmissionFile """
	commenter = models.ForeignKey(User)
	commented_file = models.ForeignKey(SubmissionFile)
	comment = models.TextField()
	selected_text = models.TextField()

class CommentRange(models.Model):
	""" The range of a given Comment, to be used by Javascript to highlight 
		the correct area of the HTML.
	"""
	comment = models.ForeignKey(Comment)
	start = models.TextField()
	end = models.TextField()
	startOffset = models.PositiveIntegerField()
	endOffset = models.PositiveIntegerField()

class CommentTag(models.Model):
	""" A tag for a given Comment. """
	comment = models.ForeignKey(Comment)
	tag = models.TextField()