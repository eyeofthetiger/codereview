import os.path
from os import listdir
import json

from django.utils import timezone

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from review.models import Submission, SubmissionFile, Course, Assignment, UserAccount, AssignedReview
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
	submissions = {}
	for assignment in assignments:
		submission = Submission.objects.filter(user=user, assignment=assignment, has_been_submitted=True).order_by('upload_date')
		if len(submission) > 0:
			submissions[assignment.id] = submission[0]
	assigned_reviews = AssignedReview.objects.filter(assigned_user=user)

	context = {
		"title": course,
		"course": course,
		"user": user,
		"assignments": assignments,
		"submissions": submissions,
		"assigned_reviews": assigned_reviews
	}

	return render(request, 'review/index.html', context)

def assignment(request, assignment_pk, submission=None, uploaded_file=None):
	""" Displays an assignment and upload form."""
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	if request.method == 'POST':
		upload_form = UploadForm(request.POST, request.FILES)
		if upload_form.is_valid():
			user = User.objects.get(username='s4108532')
			submission = Submission(
				user=user,
				assignment=assignment,
			 	upload_date=timezone.now(),
			 	has_been_submitted=False,
			 	unviewed_reviews=0,
			)
			submission.save()
			directory = os.path.join("../", "submissions", user.username, assignment.assignment_id, str(submission.id))
			os.makedirs(directory)
			submission.upload_path = directory
			submission.save()

			#if zip do whatever
			#else
			path = os.path.join(directory, request.FILES['file'].name)
			with open(path, "w") as f:
				f.write(request.FILES['file'].read())
			upload = SubmissionFile(submission=submission, file_path=path)
			upload.save()
			uploaded_file = request.FILES['file'].name

	else:
		upload_form = UploadForm()

	return render(request, 'review/assignment.html', 
		{'assignment': assignment, 'upload_form': upload_form, 'upload': uploaded_file})

def assignment_description(request, assignment_pk):
	""" Display the description of an assignment. """
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	return render(request, 'review/assignment_description.html', 
		{'title': assignment, 'assignment': assignment})

@ensure_csrf_cookie
def submission(request, assignment_pk):
	""" Displays a submission for an assignment. """
	user = User.objects.get(username='s4108532')
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	submission = Submission.objects.filter(user=user, assignment=assignment, has_been_submitted=True).order_by('upload_date')[0]
	files = SubmissionFile.objects.filter(submission=submission)
	dir_json = json.dumps({'core':{"multiple" : False,'data':get_directory_contents(submission.upload_path)}})
	return render(request, 'review/submission.html', 
		{'submission': submission, 'files': files, 'file_structure': dir_json})

def get_directory_contents(path, parent="#"):
	contents = []
	for f in listdir(path):
		new_path = os.path.join(path, f)
		
		if os.path.isdir(new_path):
			contents.append({'id':f, 'parent':parent, 'text':f})
			contents += (get_directory_contents(new_path, f))
		else:
			contents.append({'id':f, 'parent':parent, 'text':f, 'icon':False})
	return contents

def view_file(request, submission_file_pk):
	""" Displays a particular file within an assignment submission. """
	submission_file = get_object_or_404(SubmissionFile, pk=submission_file_pk)
	with open(submission_file.file_path, 'r') as f:
		file_contents = f.readlines()
	file_contents = "".join(file_contents)
	return render(request, 'review/view_file.html', 
		{'submission': submission_file.submission, 'submission_file': submission_file,
		 'file_contents': file_contents})

def review_submission(request, submission_pk):
	""" Displays the submission for review. """
	submission = get_object_or_404(Submission, pk=submission_pk)
	files = SubmissionFile.objects.filter(submission=submission)
	return render(request, 'review/submission.html', 
		{'submission': submission, 'files': files})

def get_submission_file(request):
	""" Receives an Ajax post containing a file path and returns the contents of
		that file in a json container.
	"""
	response = {}
	if request.is_ajax():
		path = request.POST.get("path")[1:] #Removes the '#' from the start of the path
		submission_id = int(request.POST.get("submission_id"))
		submission = Submission.objects.get(id=submission_id)
		path = submission.upload_path + path
	response['file_contents'] = get_file_contents(path)
	return HttpResponse(json.dumps(response), content_type="application/json")

def get_file_contents(path):
	""" Returns the contents of a file as a string. """
	with open(path, 'r') as f:
		file_contents = f.readlines()
	return "".join(file_contents)