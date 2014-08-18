from django.core.mail import send_mail, send_mass_mail, get_connection

# TODO - change this to be appropriate
FROM_EMAIL = ''

def send_email(subject, message, recipients):
	send_mail(subject, message, FROM_EMAIL, recipients)