from __future__ import absolute_import

from celery import shared_task

from django.contrib.auth.models import User

# from review.models import EmailPreferences
from review.email import send_email

@shared_task
def due_date_reached(assignment):
	# Send email to students who have selected to receive an email when an assigment is due.
	subject = assignment.name + " is due"
	message = assignment.name + " is now due. Make sure you've submitted it!"
	recipients = assignment.get_due_date_email_recipients()
	if len(recipients) > 0:
		send_email(subject, message, recipients)

	# Get submissions
	students = User.objects.filter(is_staff=False)
	submissions = []
	for student in students:
		submission = assignment.get_submission(student)
		if submission != None:
			submissions.append(submission)

	#Assign reviews


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