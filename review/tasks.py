from __future__ import absolute_import

from celery import shared_task

from django.contrib.auth.models import User

from review.email import send_email
from review.allocation import allocation
import review.models

# TODO: remove old tasks when adding new ones - http://stackoverflow.com/questions/15575826/how-to-inspect-and-cancel-celery-tasks-by-task-name

@shared_task
def due_date_reached(assignment):
	# Send email to students who have selected to receive an email when an assigment is due.
	subject = assignment.name + " is due"
	message = assignment.name + " is now due. Make sure you've submitted it!"
	recipients = assignment.get_due_date_email_recipients()
	if len(recipients) > 0:
		send_email(subject, message, recipients)
	# Get submissions and submitting students
	students = User.objects.filter(is_staff=False)

	submissions = []
	students_with_submissions = []
	assignment_authors = {}
	for student in students:
		submission = assignment.get_submission(student)
		if submission != None:
			submissions.append(submission.id)
			students_with_submissions.append(student.id)
			assignment_authors[student.id] = submission.id

	num_reviews = assignment.number_of_peer_reviews
	allocations = allocation(assignment_authors, students_with_submissions, submissions, num_reviews)

	#Assign reviews
	for user_id in allocations.keys():
		user = User.objects.get(id=user_id)
		for submission_id in allocations[user_id]:
			submission = review.models.Submission.objects.get(id=submission_id)
			assigned_review = review.models.AssignedReview(
				assigned_user=user, 
				assigned_submission=submission,
				has_been_reviewed=False,
			)
			assigned_review.save()

		prefs = review.models.EmailPreferences.objects.filter(user=user)[0]
		#Send email about review being assigned if preferences are correct.
		if prefs.on_review_assigned:
			subject = "You've been assigned a review"
			message = "You've been assigned a review"
			send_email(subject, message, [user.email])

@shared_task
def open_date_reached(assignment):
	""" Runs when an assignment becomes available. Notifies all students with 
		the appropriate settings about the new assignment.
	"""
	# Send email to students who have selected to receive an email when an assigment becomes available.
	subject = assignment.name + " released"
	message = assignment.name + " has been released. Head over to Enkidu to check it out!"
	recipients = assignment.get_open_date_email_recipients()
	if len(recipients) > 0:
		send_email(subject, message, recipients)

@shared_task
def due_date_tomorrow(assignment):
	""" Runs 24 hours before an assignment is due. Notifies all students with 
		the appropriate settings about the upcoming due date.
	"""
	# Send email to students who have selected to receive an email the day before a due date.
	subject = assignment.name + " due tomorrow"
	message = "The due date for " + assignment.name + " is in 24 hours. Don't forget to submit it!"
	recipients = assignment.get_before_due_date_email_recipients()
	if len(recipients) > 0:
		send_email(subject, message, recipients)