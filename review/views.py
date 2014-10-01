import datetime
import os.path
import json

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
from review.submission import zip_submission, get_directory_contents, get_file_contents, save_zip, save_file, is_zipfile
from review.markdown import markdown_to_html
import review.testing


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
def assignment(request, assignment_pk, submission=None, uploaded_file=None, temp_path=None):
	""" Displays an assignment upload form."""
	assignment = get_object_or_404(Assignment, pk=assignment_pk)

	if request.method == 'POST':
		if not 'test' in request.POST.keys():
			# Upload button clicked
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

				# Create temp files for testing
				temp_path = review.testing.create_temp_files(assignment, request.FILES['file'])
		else:
			# Test button clicked
			# Build context
			temp_path = request.POST['temp_path']
			upload = request.POST['upload']
			submission = get_object_or_404(Submission, pk=request.POST['submission_id'])
			upload_form = UploadForm()

			# Run tests
			review.testing.run_docker(assignment.id, temp_path, assignment.docker_command)

	else:
		upload_form = UploadForm()

	context = { 
		'title': "Submission for " + assignment.name,
		'assignment': assignment, 
		'upload_form': upload_form, 
		'upload': uploaded_file, 
		'submission': submission,
		'temp_path': temp_path
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
	prefs = EmailPreferences.objects.get(user=user)
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
		form = AssignmentForm(request.POST, request.FILES)
		if form.is_valid():
			print request.FILES
			assignment.assignment_id = form.cleaned_data['assignment_id']
			assignment.name = form.cleaned_data['name']
			assignment.description = markdown_to_html(form.cleaned_data['description_raw'])
			assignment.description_raw = form.cleaned_data['description_raw']
			assignment.open_date = form.cleaned_data['open_date']
			assignment.due_date = form.cleaned_data['due_date']
			assignment.modified_date = timezone.now()
			assignment.review_open_date = form.cleaned_data['review_open_date']
			assignment.review_due_date = form.cleaned_data['review_due_date']
			assignment.number_of_peer_reviews = form.cleaned_data['number_of_peer_reviews']
			assignment.weighting = form.cleaned_data['weighting']
			assignment.test_required = form.cleaned_data['test_required']

			# Check if test were uploaded
			test_zip = request.FILES.get('test_zip', None)
			dockerfile = request.FILES.get('dockerfile', None)
			if test_zip and dockerfile and form.cleaned_data['docker_command'] != "":
				# Deal with uploads
				directory = os.path.join("uploads", "assignment", str(assignment.id))
				if not os.path.exists(directory):
					os.makedirs(directory)
				assignment.test_zip = review.testing.save_file(test_zip, directory)
				assignment.dockerfile = review.testing.save_file(dockerfile, directory)
				assignment.docker_command = form.cleaned_data['docker_command']

				# Build the dockerfile
				review.testing.build_dockerfile(os.path.dirname(assignment.dockerfile), assignment.id)

			assignment.save()
			assignment.set_async()
			return redirect('staff')
	
	form = AssignmentForm(initial={
			'assignment_id': assignment.assignment_id,
			'name': assignment.name,
			'description_raw': assignment.description_raw,
			'open_date': assignment.open_date,
			'due_date': assignment.due_date,
			'allow_multiple_uploads': assignment.allow_multiple_uploads,
			'allow_help_centre': assignment.allow_help_centre,
			'review_open_date': assignment.review_open_date,
			'review_due_date': assignment.review_due_date,
			'number_of_peer_reviews': assignment.number_of_peer_reviews,
			'weighting': assignment.weighting,
			'test_required': assignment.test_required,
			'docker_command': assignment.docker_command,
		})

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
		form = AssignmentForm(request.POST, request.FILES)
		if form.is_valid():
			assignment = Assignment(
				assignment_id=form.cleaned_data['assignment_id'], 
				name=form.cleaned_data['name'], 
				create_date=timezone.now(), 
				modified_date=timezone.now(), 
				open_date=form.cleaned_data['open_date'], 
				due_date=form.cleaned_data['due_date'], 
				description=markdown_to_html(form.cleaned_data['description_raw']),
				description_raw=form.cleaned_data['description_raw'],
				number_of_peer_reviews=form.cleaned_data['number_of_peer_reviews'],
				review_open_date=form.cleaned_data['review_open_date'],
				review_due_date=form.cleaned_data['review_due_date'],
				weighting=form.cleaned_data['weighting'],
				test_required=form.cleaned_data['test_required'],
				allow_multiple_uploads=form.cleaned_data['allow_multiple_uploads'],
				allow_help_centre=form.cleaned_data['allow_help_centre'],	
			)
			assignment.save()

			# Check if test were uploaded
			test_zip = request.FILES.get('test_zip', None)
			dockerfile = request.FILES.get('dockerfile', None)
			if test_zip and dockerfile and form.cleaned_data['docker_command'] != "":
				# Deal with uploads
				directory = os.path.join("uploads", "assignment", str(assignment.id))
				if not os.path.exists(directory):
					os.makedirs(directory)
				assignment.test_zip = review.testing.save_file(test_zip, directory)
				assignment.dockerfile = review.testing.save_file(dockerfile, directory)
				assignment.docker_command = form.cleaned_data['docker_command']

				# Build the dockerfile
				review.testing.build_dockerfile(os.path.dirname(assignment.dockerfile), assignment.id)

			assignment.save()
			assignment.set_async()
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
			now = timezone.now()
			question = Question(
				user=user,
				title=form.data['title'], 
				text=markdown_to_html(form.data['text_raw']),
				text_raw=form.data['text_raw'],
				create_date=now, 
				modified_date=now,
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
def edit_question(request, question_pk):
	""" Displays a form for creating a new Question on the forum. """

	user = request.user
	question = get_object_or_404(Question, pk = question_pk)

	if question.user != user:
		return redirect('index')

	if request.method == 'POST':
		form = QuestionForm(request.POST)
		if form.is_valid():
			question.title=form.data['title']
			question.text=markdown_to_html(form.data['text_raw'])
			question.text_raw=str(form.data['text_raw']),
			question.modified_date=timezone.now()
			question.save()
		return redirect('question', question_pk=question.id)
	else:
		form = QuestionForm(instance=question)

	context = {
		'title': 'Edit question',
		'question': question,
		'form': form
	}

	return render(request, 'review/edit_question.html', context)

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
				text=markdown_to_html(form.data['text']), 
				text_raw=form.data['text'],
				create_date=timezone.now(), 
				modified_date=timezone.now(),
			)
			response.save()
			# Send email to Questioner about the new answer.
			if not response.question.user.is_staff:
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

def is_allowed_to_review(user, submission):
	""" Returns true if the given user is allowed to review the given submission
		and they haven't already reviewed it. Returns false otherwise.
	"""
	assigned_review = AssignedReview.objects.filter(assigned_user=user,
	 assigned_submission=submission, has_been_reviewed=False)
	if len(assigned_review) > 0:
		return True
	return False