import os.path
from os import listdir
import json
from zipfile import ZipFile, is_zipfile
import datetime

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from review.models import Submission, SubmissionFile, Course, Assignment, \
	AssignedReview, Comment, CommentRange, EmailPreferences, Question, Response
from review.forms import UploadForm, AssignmentForm, QuestionForm, ResponseForm, EmailPreferencesForm
from review.email import send_email

@login_required
def index(request):
	""" Displays the appropriate dashboard for the current user. """

	user = request.user
	# Redirect if user is staff
	if user.is_staff:
		return redirect('staff')
	course = Course.objects.get(id=1) # There should only be a single course

	# Get all assignments with an open date prior to the current time.
	assignments = Assignment.objects.filter(
		open_date__lte=timezone.now()).order_by('due_date')

	# Get all submissions by the user
	submissions = {}
	for assignment in assignments:
		submission = assignment.get_submission(user)
		if submission:
			submissions[assignment.id] = submission
	# Get all assigned reviews for the user
	assigned_reviews = AssignedReview.objects.filter(assigned_user=user)
	# Get all questions for forum
	questions = Question.objects.order_by('create_date')

	context = {
		"title": course,
		"course": course,
		"user": user,
		"assignments": assignments,
		"submissions": submissions,
		"assigned_reviews": assigned_reviews,
		"questions": questions
	}

	return render(request, 'review/index.html', context)

@login_required
def staff(request):
	""" Displays the appropriate dashboard for course staff. """

	user = request.user
	#Redirect if user is not staff
	if not user.is_staff:
		return redirect('index')

	course = Course.objects.get(id=1)
	assignments = Assignment.objects.all()

	# Get all questions for forum
	questions = Question.objects.order_by('create_date')

	context = {
		"title": course,
		"course": course,
		"user": user,
		"assignments": assignments,
		"questions": questions,
	}

	return render(request, 'review/staff.html', context)

@login_required
def email_preferences(request):
	""" Displays the settings page for a User's email preferences. """
	user = request.user
	# Redirect if user is staff
	if user.is_staff:
		return redirect('staff')

	prefs = EmailPreferences.objects.filter(user=user)[0]

	if request.method == 'POST':
		form = EmailPreferencesForm(request.POST)
		if form.is_valid():
			prefs.on_upload = form.data.get('on_upload', False)
			prefs.on_submission = form.data.get('on_submission', False)
			prefs.on_due_date = form.data.get('on_due_date', False)
			prefs.on_open_date = form.data.get('on_open_date', False)
			prefs.on_review_received = form.data.get('on_review_received', False)
			prefs.on_review_assigned = form.data.get('on_review_assigned', False)
			prefs.on_question_answered = form.data.get('on_question_answered', False)
			prefs.on_question_asked = form.data.get('on_question_asked', False)
			prefs.on_upload = form.data.get('on_upload', False)
			prefs.save()
		return redirect('index')
	else:
		form = EmailPreferencesForm(instance=prefs)

	context = {
		"title": 'Email Preferences',
		"user": user,
		"form": form
	}
	return render(request, 'review/email_preferences.html', context)


@login_required
def assignment(request, assignment_pk, submission=None, uploaded_file=None):
	""" Displays an assignment upload form."""
	assignment = get_object_or_404(Assignment, pk=assignment_pk)

	if request.method == 'POST':
		upload_form = UploadForm(request.POST, request.FILES)
		if upload_form.is_valid():
			user = request.user
			submission = Submission(
				user=user,
				assignment=assignment,
			 	upload_date=timezone.now(),
			 	has_been_submitted=False,
			 	unviewed_reviews=0,
			)
			submission.save()
			#Directory for submission upload
			directory = os.path.join("submissions", user.username,
			 assignment.assignment_id, str(submission.id))
			os.makedirs(directory)
			submission.upload_path = directory
			submission.save()

			#Check if upload is zip file and take appropriate action
			u_file = request.FILES['file']
			if u_file.name.endswith('.zip'):
				if is_zipfile(u_file):
					uploaded_file = save_zip(u_file, submission)
				else:
					return render(request, 'review/assignment.html', 
						{	
							'title': "Submission for " + assignment,
							'assignment': assignment,
							'upload_form': upload_form, 
							'upload': None,
							'submission': None,
							'error_message': "The file '" + u_file.name + 
							"' is not a valid Zip file."
						})
			else:
				uploaded_file = save_file(request.FILES['file'], submission)

	else:
		upload_form = UploadForm()

	context = { 
		'title': "Submission for " + assignment.name,
		'assignment': assignment, 
		'upload_form': upload_form, 
		'upload': uploaded_file, 
		'submission': submission,
	}

	return render(request, 'review/assignment.html', context)

@login_required
def submit_assignment(request, submission_pk):
	""" This page gives a message to the user informaing them of a successful
		submission.
	"""
	user = request.user
	# Redirect if user is staff
	if user.is_staff:
		return redirect('staff')
	submission = get_object_or_404(Submission, pk=submission_pk)
	# Redirect if user is not the submitter
	if user != submission.user:
		return redirect('index')
	submission.has_been_submitted = True
	submission.save()

	# Send success email
	prefs = EmailPreferences.objects.get(user=user)[0]
	if prefs.on_submission:
		subject = "Submission for " + submission.assignment.name
		message = "You're submission was successful."
		send_email(subject, message, [submission.user.email])

	context = {	
		'title': submission.assignment.name + " submitted",
		'submission': submission
	}

	return render(request, 'review/submission_success.html', context)

@login_required
def assignment_description(request, assignment_pk):
	""" Display the description of an assignment. """
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	return render(request, 'review/assignment_description.html', 
		{'title': assignment, 'assignment': assignment})

@login_required
@ensure_csrf_cookie
def submission(request, submission_pk):
	""" Displays the given submission. If the user is the reviewer, enables 
		commenting. 
	"""
	user = request.user
	submission = get_object_or_404(Submission, pk=submission_pk)
	reviews = AssignedReview.objects.filter(
		assigned_submission=submission, has_been_reviewed=True)
	reviews = [{'id':r.id, 'user_id':r.assigned_user.id} for r in reviews]
	comments = {}
	is_owner = (submission.user == user)
	if not is_owner and not is_allowed_to_review(user, submission):
		print "TODO: deal with unauthorised access of submissions"
	files = SubmissionFile.objects.filter(submission=submission)
	# Builds JSON representation of the submission directory
	dir_json = json.dumps(
		{'core':{
			"multiple" : False,
			'data':get_directory_contents(submission.upload_path)
		}
	})
	return render(request, 'review/submission.html', {
			'submission': submission, 
			'files': files, 
			'file_structure': dir_json,
			'is_owner': is_owner,
			'reviews': reviews,
			'user': user
		})

@login_required
def list_submissions(request, assignment_pk):
	""" List all submissions by students for a particular assignment. """
	user = request.user
	#Redirect if not staff
	if not user.is_staff:
		return redirect('index')

	course = Course.objects.get(id=1)
	assignment = get_object_or_404(Assignment, pk=assignment_pk)
	students = User.objects.filter(is_staff=False)
	submissions = {}
	for student in students:
		student_submissions = Submission.objects.filter(
			user=student, 
			assignment=assignment, 
			has_been_submitted=True
		).order_by('-upload_date')
		if len(student_submissions) == 0:
			submissions[student] = None
		else:
			submissions[student] = student_submissions[0]
	context = {
		'title': "Submissions for " + assignment.name,
		'assignment': assignment, 
		'submissions': submissions,
		'students': students,
		'course': course,
	}
	return render(request, 'review/list_submissions.html', context)

@login_required
def edit_assignment(request, assignment_pk):
	""" Displays the settings of an assignment and allows the user to edit them 
		if they have the authority.
	"""
	user = request.user
	#Redirect if not staff
	if not user.is_staff:
		return redirect('index')

	assignment = get_object_or_404(Assignment, pk=assignment_pk)

	if request.method == 'POST':
		form = AssignmentForm(request.POST)
		if form.is_valid():
			assignment.name = form.data['name']
			assignment.description = form.data['description']
			assignment.open_date = form.data['open_date']
			assignment.due_date = form.data['due_date']
			assignment.modified_date = timezone.now()
			assignment.save()
		return redirect('staff')
	else:
		form = AssignmentForm(instance=assignment)

	context = { 
		'title': "Editing " + assignment.name,
		'assignment': assignment,
		'form': form
	}
	return render(request, 'review/edit_assignment.html', context)

@login_required
def add_assignment(request):
	""" Displays a page with a form for the creation of a new assignment by 
		the course staff.
	"""
	user = request.user
	#Redirect if not staff
	if not user.is_staff:
		return redirect('index')

	if request.method == 'POST':
		form = AssignmentForm(request.POST)
		if form.is_valid():
			assignment = Assignment(
				assignment_id=form.data['assignment_id'], 
				name=form.data['name'], 
				create_date=timezone.now(), 
				modified_date=timezone.now(), 
				open_date=form.data['open_date'], 
				due_date=form.data['due_date'], 
				description=form.data['description'],
				number_of_peer_reviews=form.data['number_of_peer_reviews'],
				review_open_date=form.data['review_open_date'],
				review_due_date=form.data['review_due_date'],
				weighting=form.data['weighting'],	
			)
			# Get booleans. If false they aren't in the form dict.
			assignment.test_required = form.data.get('test_required', False)
			assignment.has_tests = form.data.get('has_tests', False)
			assignment.allow_multiple_uploads = form.data.get(
				'allow_multiple_uploads', False)
			assignment.allow_help_centre = form.data.get(
				'allow_help_centre', False)
			assignment.save()
		return redirect('staff')
	else:
		form = AssignmentForm()

	context = {
		'title': 'Add an assignment',
		'form': form
	}

	return render(request, 'review/add_assignment.html', context)

@login_required
def download(request, submission_pk):
	""" Downloads the sumbission represented by the given primary key. The
		submission is packaged in a zip file.
	"""
	user = request.user
	#Redirect if not staff
	if not user.is_staff:
		return redirect('index')
	submission = get_object_or_404(Submission, pk=submission_pk)
	download_path = zip_submission(submission)
	download = open(download_path, 'r')
	response = HttpResponse(download, mimetype='application/zip')
	response['Content-Disposition'] = 'attachment; filename=' + download_path
	return response

@login_required
def add_question(request):
	""" Displays a form for creating a new Question on the forum. """
	user = request.user

	if request.method == 'POST':
		form = QuestionForm(request.POST)
		if form.is_valid():
			question = Question(
				user=user,
				title=form.data['title'], 
				text=form.data['text'], 
				create_date=timezone.now(), 
				modified_date=timezone.now(),
			)
			question.save()
		return redirect('index')
	else:
		form = QuestionForm()

	context = {
		'title': 'Add a question',
		'form': form
	}

	return render(request, 'review/add_question.html', context)

@login_required
def question(request, question_pk):
	""" Displays a question, its associated responses and a form for users to
		post their own response.
	"""
	user = request.user
	question = get_object_or_404(Question, pk = question_pk)
	responses = Response.objects.filter(question=question)
	if request.method == 'POST':
		form = ResponseForm(request.POST)
		if form.is_valid():
			response = Response(
				user=user,
				question=question,
				text=form.data['text'], 
				create_date=timezone.now(), 
				modified_date=timezone.now(),
			)
			response.save()
				# Send success email
			prefs = EmailPreferences.objects.get(user=response.question.user)
			if prefs.on_question_answered:
				subject = "New answer for your question"
				message = "Someone has posted a new answer to your question."
				send_email(subject, message, [response.question.user.email])
		return redirect('question', question.id)
	else:
		form = ResponseForm()
		context = {
			'title': question.title,
			'form': form,
			'question': question,
			'responses': responses,
			'user': user
		}

	return render(request, 'review/question.html', context)

@login_required
def sticky(request, question_pk):
	""" Switches the sticky status of the given response. """
	user = request.user
	if user.is_staff:
		question = get_object_or_404(Question, pk = question_pk)
		if question.stickied:
			question.stickied = False
		else:
			question.stickied = True
		question.save()
		return redirect('staff')
	else:
		return redirect('index')

@login_required
def set_as_answer(request, response_pk):
	""" Switches the answer status of the given question. """
	user = request.user
	response = get_object_or_404(Response, pk = response_pk)
	if response.question.user == user:
		if response.selected_answer:
			response.selected_answer = False
		else:
			response.selected_answer = True
		response.save()
	return redirect('question', response.question.id)


def zip_submission(submission):
	""" Receives a Submission object, get all the files of the submission and 
		puts them as a zip file retaining the original structure of the
		submission. The path to the zip file is then returned.
	"""
	if not os.path.isdir(os.path.join('temp', 'downloads')):
		os.makedirs(os.path.join('temp', 'downloads'))
	submission_files = SubmissionFile.objects.filter(submission=submission)
	zip_path = os.path.join('temp', 'downloads', (str(timezone.now()) + ".zip"))
	with ZipFile(zip_path, 'w') as zipfile:
		for f in submission_files:
			zipfile.write(os.path.join(submission.upload_path, f.file_path),
			 f.file_path)
	return zip_path

def get_directory_contents(path, parent="#"):
	""" Gets the contents of a directory and returns it as a list. """
	contents = []
	for f in listdir(path):
		new_path = os.path.join(path, f)
		if os.path.isdir(new_path):
			contents.append({'id':f, 'parent':parent, 'text':f, 'icon':False})
			contents += (get_directory_contents(new_path, f))
		else:
			contents.append({'id':f, 'parent':parent, 'text':f, 'icon':False})
	return contents

def get_submission_file(request):
	""" Receives an Ajax post containing a file path and returns the contents of
		that file in a json container, along with the id of its corresponding
		SubmissionFile object.
	"""
	response = {}
	if request.is_ajax():
		#[1:] Removes the '#' from the start of the path
		path = request.POST.get("path")[1:]
		submission_id = int(request.POST.get("submission_id"))
		submission = Submission.objects.get(id=submission_id)
		submissionFile = SubmissionFile.objects.filter(
			submission=submission, file_path=path[1:])
		path = submission.upload_path + path
		response['submission_file_id'] = submissionFile[0].id
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
	submission_file = SubmissionFile(
		submission=submission, file_path=upload.name)
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
	#TODO - build up larger list of files/folders to ignore
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
	assigned_review = AssignedReview.objects.filter(assigned_user=user,
	 assigned_submission=submission, has_been_reviewed=False)
	if len(assigned_review) > 0:
		return True
	return False
