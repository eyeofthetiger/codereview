from django.utils import timezone

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from review.models import Submission, SubmissionFile, Course, Assignment
from review.forms import UploadForm

def index(request):
	""" Displays the appropriate dashboard for the current user. """

	# Get fake user for testing
	user = User.objects.get(username='s4108532')

	# if teacher:
	# 	go to teacher page

	# Get fake course for testing. This assumes that only a single course can be active at a time.
	course = Course.objects.get(id=1)
	# Get all assignments with an open date prior to the current time.
	assignments = Assignment.objects.filter(open_date__lte=timezone.now()).order_by('due_date')

	context = {
		"title": course,
		"course": course,
		"user": user,
		"assignments": assignments,
	}

	return render(request, 'review/index.html', context)

def assignment(request, assignment_pk):
	""" Displays an assignment and upload form."""
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	if request.method == 'POST':
		form = UploadForm(request.POST, request.FILES)
		if form.is_valid():
			user = User.objects.get(username='test')
			submission = Submission(user=user, assignment=assignment, date=timezone.now())
			submission.save()
			upload = SubmissionFile(submission=submission, submission_file=request.FILES['file'])
			upload.save()
			return HttpResponseRedirect('/assignment/', assignment_pk)
	else:
		form = UploadForm()
	return render(request, 'review/assignment.html', 
		{'assignment': assignment, 'form': form})

def assignment_description(request, assignment_pk):
	""" Display the description of an assignment. """
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	return render(request, 'review/assignment_description.html', 
		{'title': assignment, 'assignment': assignment})

def submission(request, submission_pk):
	""" Displays a submission for an assignment. """
	submission = get_object_or_404(Submission, pk=submission_pk)
	files = SubmissionFile.objects.filter(submission=submission)
	return render(request, 'review/submission.html', 
		{'submission': submission, 'files': files})

def view_file(request, assignment_pk, submission_pk, submission_file_pk):
	""" Displays a particular file within an assignment submission. """
	submission = get_object_or_404(Submission, pk=submission_pk)
	submission_file = get_object_or_404(SubmissionFile, pk=submission_file_pk)
	with open(submission_file.get_path(), 'r') as f:
		file_contents = f.readlines()
	file_contents = "".join(file_contents)
	return render(request, 'review/view_file.html', 
		{'submission': submission, 'submission_file': submission_file,
		 'file_contents': file_contents})

def add_assignment():
	pass

def view_help_centre():
	pass

def add_question():
	pass