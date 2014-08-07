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
	user = User.objects.get(username='test')

	# if teacher:
	# 	go to teacher page

	# Get fake course for testing. This assumes that only a single course can be active at a time.
	course = Course.objects.get(id=1)

	assignments = Assignment.objects.filter(course=course)

	context = {
		"course": course,
		"user": user,
		"assignments": assignments,
	}

	return render(request, 'review/index.html', context)

def assignment(request, assignment_id):
	""" Displays an assignment and upload form."""
	assignment = get_object_or_404(Assignment, pk=assignment_id)
	if request.method == 'POST':
		form = UploadForm(request.POST, request.FILES)
		if form.is_valid():
			user = User.objects.get(username='test')
			submission = Submission(user=user, assignment=assignment, date=timezone.now())
			submission.save()
			upload = SubmissionFile(submission=submission, submission_file=request.FILES['file'])
			upload.save()
			return HttpResponseRedirect('/assignment/', assignment_id)
	else:
		form = UploadForm()
	return render(request, 'review/assignment.html', 
		{'assignment': assignment, 'form': form})

def submission(request, submission_id):
	""" Displays a submission for an assignment. """
	submission = get_object_or_404(Submission, pk=submission_id)
	files = SubmissionFile.objects.filter(submission=submission)
	return render(request, 'review/submission.html', 
		{'submission': submission, 'files': files})

def view_file(request, assignment_id, submission_id, submission_file_id):
	""" Displays a particular file within an assignment submission. """
	submission = get_object_or_404(Submission, pk=submission_id)
	submission_file = get_object_or_404(SubmissionFile, pk=submission_file_id)
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