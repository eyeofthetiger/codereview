from datetime import timedelta, datetime
import time
import os.path

from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

import tasks

""" This file contains Model descriptions for database tables. """

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
	description_raw = models.TextField()
	allow_multiple_uploads = models.BooleanField()
	allow_help_centre = models.BooleanField()
	number_of_peer_reviews = models.IntegerField()
	review_open_date = models.DateTimeField()
	review_due_date = models.DateTimeField()
	weighting = models.IntegerField()
	test_zip = models.TextField(blank=True)
	dockerfile = models.TextField(blank=True)
	docker_command = models.TextField(blank=True)
	test_required = models.BooleanField()

	def __unicode__(self):
		return str(self.name)

	def has_tests(self):
		if len(self.test_zip) == 0 or len(self.dockerfile) == 0 \
			or len(self.docker_command) == 0:
			return False
		return True

	def was_submitted(self, user):
		""" Returns true if the given user had a submission for this assignment.
		"""
		submissions = Submission.objects.filter(user=user, assignment=self,
		 has_been_submitted=True)
		if len(submissions) > 0:
			return True
		return False

	def due_date_passed(self):
		""" Returns true if due date has passed, false otherwise. """
		return self.due_date < timezone.now()

	def is_before_open_date(self):
		""" Returns true if before open date, false otherwise. """
		return self.open_date > timezone.now()

	def get_submission(self, user):
		""" Returns the latest Submission for this assignment by a given 
			User. 
		"""
		submissions = Submission.objects.filter(user=user, assignment=self,
		 has_been_submitted=True).order_by('-upload_date')
		if len(submissions) > 0:
			return submissions[0]
		return None

	def set_async(self):
		""" Set the async triggers for this Assignment. """
		print "Setting async"
		now = timezone.now()
		if self.open_date >= now:
			tasks.open_date_reached.apply_async(args=(self,), eta=self.open_date)
		if self.get_before_due_date() >= now:
			tasks.due_date_tomorrow.apply_async(args=(self,), 
				eta=self.get_before_due_date())
		if self.due_date >= now:
			tasks.due_date_reached.apply_async(args=(self,), eta=self.due_date)

	def get_before_due_date(self):
		""" Return the datetime 24 hours before the due date. """
		return self.due_date - timedelta(days=1)

	def get_open_date_email_recipients(self):
		""" Returns a list of users who will receive an email when the open date
			occurs. Note: This is not really the most logical place for this 
			function, but due to a bug when using Django and Celery, it's the
			only place I could put it and get it to work.
		"""
		return [pref.user.email for pref in EmailPreferences.objects.filter(
			on_open_date=True) if not pref.user.is_staff]

	def get_before_due_date_email_recipients(self):
		""" Returns a list of users who will receive an email 24 hours before 
			the due date . Note: This is not really the most logical place for 
			this function, but due to a bug when using Django and Celery, it's 
			the only place I could put it and get it to work.
		"""
		return [pref.user.email for pref in \
			review.models.EmailPreferences.objects.filter(
				on_day_before_due=True) if not pref.user.is_staff]

	def get_due_date_email_recipients(self):
		""" Returns a list of users who will receive an email when the due date
			occurs. Note: This is not really the most logical place for this 
			function, but due to a bug when using Django and Celery, it's the
			only place I could put it and get it to work.
		"""
		return [pref.user.email for pref in \
			EmailPreferences.objects.filter(
				on_due_date=True) if not pref.user.is_staff]

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

class EmailPreferences(models.Model):
	""" Individual preferences of when a user would like to receive email 
		alerts.
	"""
	user = models.ForeignKey(User)
	on_upload = models.BooleanField(default=False)
	on_submission = models.BooleanField(default=True)
	on_day_before_due = models.BooleanField(default=False)
	on_due_date = models.BooleanField(default=False)
	on_open_date = models.BooleanField(default=True)
	on_review_received = models.BooleanField(default=True)
	on_review_assigned = models.BooleanField(default=True)
	on_question_answered = models.BooleanField(default=True)
	on_question_asked = models.BooleanField(default=False)

class Comment(models.Model):
	""" A Commment made by a User on a particular SubmissionFile """
	commenter = models.ForeignKey(User)
	commented_file = models.ForeignKey(SubmissionFile)
	comment = models.TextField()
	selected_text = models.TextField()

	def __unicode__(self):
		return str(self.comment)

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

class Question(models.Model):
	""" A question posted by a user. """
	user = models.ForeignKey(User)
	title = models.CharField(max_length=140)
	text = models.TextField()
	text_raw = models.TextField()
	create_date = models.DateTimeField()
	modified_date = models.DateTimeField()
	stickied = models.BooleanField(default=False)

	def __unicode__(self):
		return str(self.title)

	def number_of_responses(self):
		""" Returns the number of responses associated with a Question. """
		return len(Response.objects.filter(question=self))

	def is_staff(self):
		""" Returns true if the creator of the question is staff,
			false otherwise.
		"""
		return self.user.is_staff

	def has_answer(self):
		""" Returns true if the question has a response that has been selected 
			as a definitive answer.
		"""
		responses = Response.objects.filter(question=self, selected_answer=True)
		if(len(responses) > 0):
			return True
		return False

	def get_comments(self):
		""" Returns a list of all comments for this question. """
		return QuestionComment.objects.filter(question=self)

	def edited(self):
		""" Return true if the question has been edited, false otherwise. """
		return self.create_date != self.modified_date

class Response(models.Model):
	""" A response to a Question posted by a user. """
	user = models.ForeignKey(User)
	question = models.ForeignKey(Question)
	text = models.TextField()
	text_raw = models.TextField()
	create_date = models.DateTimeField()
	modified_date = models.DateTimeField()
	selected_answer = models.BooleanField(default=False)

	def __unicode__(self):
		return str(self.text)

	def is_staff(self):
		""" Returns true if the creator of the response is staff,
			false otherwise.
		"""
		return self.user.is_staff

	def get_user(self):
		""" Returns the user who created this post. If they are a student, the 
			string 'Anonymous' is returned unless settings indicate they user
			name can be displayed.
		"""
		if not self.user.is_staff:
			return "Anonymous"
		return self.user

	def get_comments(self):
		""" Returns a list of all comments for this response. """
		return ResponseComment.objects.filter(response=self)

class QuestionComment(models.Model):
	""" A comment on a Question in the forum. """
	user = models.ForeignKey(User)
	question = models.ForeignKey(Question)
	text = models.TextField()
	text_raw = models.TextField()
	create_date = models.DateTimeField()
	modified_date = models.DateTimeField()

class ResponseComment(models.Model):
	""" A comment on a Response in the forum. """
	user = models.ForeignKey(User)
	response = models.ForeignKey(Response)
	text = models.TextField()
	text_raw = models.TextField()
	create_date = models.DateTimeField()
	modified_date = models.DateTimeField()
