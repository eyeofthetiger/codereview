from django import forms
from review.models import Assignment

class UploadForm(forms.Form):
	file = forms.FileField(label='Select a file')

class AssignmentEditForm(forms.ModelForm):
	""" A form for editing an assignment after it has been created. """
	class Meta:
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

class AssignmentForm(forms.ModelForm):
	""" A form for the creation of an assignment. """

	# allow_multiple_uploads = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=True)
	# allow_help_centre = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=True)
	# has_tests = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=True)
	# test_required = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=True)

	class Meta:
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