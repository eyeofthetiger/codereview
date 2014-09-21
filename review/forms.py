from django import forms

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
			'text'
		]
		
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

class AssignmentForm(forms.ModelForm):
	""" A form for the creation or editing of an assignment. """

	class Meta:
		""" Builds the form from the Assignment model. """
		model = Assignment
		fields = [
			'assignment_id',
			'name', 
			'description', 
			'open_date', 
			'due_date', 
			'allow_multiple_uploads', 
			'allow_help_centre',
			'number_of_peer_reviews',
			'review_open_date',
			'review_due_date',
			'weighting',
			'has_tests',
			'test_required',
		]