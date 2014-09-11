from django.core.mail import send_mail, send_mass_mail, get_connection
from django.conf import settings

def send_email(subject, message, recipients):
	""" Sends an email with the given subject and mesage to a list of 
		recipients.
	"""
	send_mail(subject, message, settings.FROM_EMAIL, recipients)