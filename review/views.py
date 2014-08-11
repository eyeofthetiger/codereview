import os.path
from os import listdir
import json
from zipfile import ZipFile, is_zipfile

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
	# Get all submissions by the user
	submissions = {}
	for assignment in assignments:
		submission =  assignment.get_submission(user)
		if submission:
			submissions[assignment.id] = submission
	# Get all assigned reviews for the user
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

			if request.FILES['file'].name.endswith('.zip'):
				if is_zipfile(request.FILES['file']):
					uploaded_file = save_zip(request.FILES['file'], submission)
				else:
					# TODO: Deal with broken zip files
					pass
			else:
				uploaded_file = save_file(request.FILES['file'], submission)

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
def submission(request, submission_pk):
	""" Displays the given submission. If the user is the reviewer, enables 
		commenting. 
	"""
	user = User.objects.get(username='s4108532')
	submission = get_object_or_404(Submission, pk=submission_pk)
	is_owner = (submission.user == user)
	if not is_owner and not is_allowed_to_review(user, submission):
		print "TODO: deal with unauthorised access of submissions"
	files = SubmissionFile.objects.filter(submission=submission)
	dir_json = json.dumps({'core':{"multiple" : False,'data':get_directory_contents(submission.upload_path)}})
	return render(request, 'review/submission.html', {
			'submission': submission, 
			'files': files, 
			'file_structure': dir_json,
			'is_owner': is_owner
		})

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

def save_file(upload, submission):
	""" Receives an uploaded file, and a Submission object. Writes the
		uploaded file to the correct path and stores a new SubmissionFile object
		in the database. Returns the filename.
	"""
	path = os.path.join(submission.upload_path, upload.name)
	with open(path, "w") as f:
		f.write(upload.read())
	submission_file = SubmissionFile(submission=submission, file_path=upload.name)
	submission_file.save()
	return upload.name

def save_zip(zip_file, submission):
	""" Receives a zip file. Extracts all valid files and creates a 
		SubmissionFile for each in the database. Returns the zip file name. 
	"""
	with ZipFile(zip_file, 'r') as zip_object:
		for f in [x for x in zip_object.namelist() if is_valid_file(x)]:
			zip_object.extract(f, path=submission.upload_path)
			submission_file = SubmissionFile(submission=submission, file_path=f)
			submission_file.save()
	return zip_file.name

def is_valid_file(file_path):
	""" Returns false if it is an invalid file (e.g. *.pyc), or in an invalid
		folder (e.g. /.git/). Returns true otherwise.
	"""
	invalid_dirs = ['__MACOSX','.git']
	file_path = os.path.normpath(file_path) #Normalise path
	path_list = file_path.split(os.sep)
	if file_path.endswith(".DS_Store") or file_path.endswith(".pyc"):
		return False
	if len([x for x in invalid_dirs if x in path_list]) > 0:
		return False
	return True

def is_allowed_to_review(user, submission):
	""" Returns true if the given user is allowed to review the given submission
		and they haven't already reviewed it. Returns false otherwise.
	"""
	assigned_review = AssignedReview.objects.filter(assigned_user=user, assigned_submission=submission, has_been_reviewed=False)
	if len(assigned_review) > 0:
		return True
	return False