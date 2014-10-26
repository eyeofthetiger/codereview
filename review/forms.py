from datetime import datetime

from django import forms
from django.utils import timezone

from review.models import Assignment, EmailPreferences, Question


""" This file contains forms to be used throughout the codereview app. """

class UploadForm(forms.Form):
	""" A form for the uploading of a Submission. """
	file = forms.FileField(label='Select a file')

class QuestionForm(forms.ModelForm):
	""" A form for the creation of Questions in the question forum. """
	class Meta:
		""" Builds the form from the Question model. """
		model = Question
		fields = [
			'title',
			'text_raw'
		]
		labels = {
            'text_raw': "Text",
        }
		
class ResponseForm(forms.Form):
	""" A form for the creation of a Response to a Question in the  forum. """
	text = forms.CharField(label='Response', widget=forms.Textarea)

class EmailPreferencesForm(forms.ModelForm):
	""" A form for the setting of user email preferences. """
	class Meta:
		""" Builds the form from the EmailPreferences model. """
		model = EmailPreferences
		fields = [
			'on_upload',
			'on_submission',
			'on_due_date',
			'on_open_date',
			'on_review_received',
			'on_review_assigned',
			'on_question_answered',
			'on_question_asked',
		]

class AssignmentForm(forms.Form):
	""" A form for the creation or editing of an assignment. """

	assignment_id = forms.CharField(max_length=140) #Unique ID for assignment
	name = forms.CharField(max_length=140)
	open_date = forms.CharField()
	due_date = forms.CharField()
	description_raw = forms.CharField(
		label='Description', widget=forms.Textarea)
	allow_multiple_uploads = forms.BooleanField(required=False)
	allow_help_centre = forms.BooleanField(required=False)
	number_of_peer_reviews = forms.IntegerField()
	review_open_date = forms.CharField()
	review_due_date = forms.CharField()
	weighting = forms.IntegerField()
	test_zip = forms.FileField(required=False)
	dockerfile = forms.FileField(required=False)
	docker_command = forms.CharField(required=False)
	test_required = forms.BooleanField(required=False)

	def format_date(self, date_str):
		""" Takes a string in the format DD-MM-YYYY HH:MM and converts it to 
			datetime format. """
		d = datetime.strptime(date_str, "%d-%m-%Y %H:%M")
		return timezone.make_aware(d, timezone.get_current_timezone())

	def clean_due_date(self):
		""" Convert due date representation to format readable by Django. """
		data = self.cleaned_data['due_date']
		return self.format_date(data)

	def clean_open_date(self):
		""" Convert open date representation to format readable by Django. """
		data = self.cleaned_data['open_date']
		return self.format_date(data)

	def clean_review_due_date(self):
		""" Convert review due date representation to format readable by 
			Django. 
		"""
		data = self.cleaned_data['review_due_date']
		return self.format_date(data)

	def clean_review_open_date(self):
		""" Convert review open date representation to format readable by 
			Django. 
		"""
		data = self.cleaned_data['review_open_date']
		return self.format_date(data)
