import os.path
from os import listdir
import json
from zipfile import ZipFile, is_zipfile
import datetime

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from review.models import Submission, SubmissionFile, Course, Assignment, UserAccount, AssignedReview, Comment, CommentRange, EmailPreferences
from review.forms import UploadForm
from review.email import send_email

def index(request):
	""" Displays the appropriate dashboard for the current user. """

	# Get fake user for testing
	user = User.objects.get(username='user1')
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
			user = User.objects.get(username='user1')
			submission = Submission(
				user=user,
				assignment=assignment,
			 	upload_date=timezone.now(),
			 	has_been_submitted=False,
			 	unviewed_reviews=0,
			)
			submission.save()
			directory = os.path.join( "submissions", user.username, assignment.assignment_id, str(submission.id))
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
		{'assignment': assignment, 'upload_form': upload_form, 'upload': uploaded_file, 'submission': submission})

def submit_assignment(request, submission_pk):
	""" This page gives a message to the user informaing them of a successful
		submission.
	"""
	submission = get_object_or_404(Submission, pk=submission_pk)
	submission.has_been_submitted = True
	submission.save()
	return render(request, 'review/submission_success.html', {'submission': submission})

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
	# TODO, put proper user
	user = User.objects.get(username='user1')
	submission = get_object_or_404(Submission, pk=submission_pk)
	reviews = AssignedReview.objects.filter(assigned_submission=submission, has_been_reviewed=True)
	reviews = [{'id':r.id, 'user_id':r.assigned_user.id} for r in reviews]
	comments = {}
	is_owner = (submission.user == user)
	if not is_owner and not is_allowed_to_review(user, submission):
		print "TODO: deal with unauthorised access of submissions"
	files = SubmissionFile.objects.filter(submission=submission)
	dir_json = json.dumps({'core':{"multiple" : False,'data':get_directory_contents(submission.upload_path)}})
	return render(request, 'review/submission.html', {
			'submission': submission, 
			'files': files, 
			'file_structure': dir_json,
			'is_owner': is_owner,
			'reviews': reviews,
			'user': user.id # TODO, put proper user
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
		that file in a json container, along with the id of its corresponding
		SubmissionFile object.
	"""
	response = {}
	if request.is_ajax():
		path = request.POST.get("path")[1:] #Removes the '#' from the start of the path
		submission_id = int(request.POST.get("submission_id"))
		submission = Submission.objects.get(id=submission_id)
		submissionFile = SubmissionFile.objects.filter(submission=submission, file_path=path[1:])
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

def api_root(request):
	""" Returns information about the annotator API. """
	response = { "name": "Annotator Store API", "version": "2.0.0" }
	return HttpResponse(json.dumps(response), content_type="application/json")

@csrf_exempt
def api_index(request):
	""" If request type is GET, returns a list of all annotations. If request 
		type is POST, stores posted annotation.
	"""
	if request.method == 'POST':
		#Save comment
		comment_data = json.loads(request.body)
		submission_file_pk, user_pk = comment_data['uri'].split("+")
		submission_file = get_object_or_404(SubmissionFile, pk = submission_file_pk)
		user = get_object_or_404(User, pk = user_pk)
		comment = Comment(
			commenter = user, 
			commented_file = submission_file, 
			selected_text = comment_data['quote'],
			comment = comment_data['text']
		)
		comment.save()
		for ranges in comment_data['ranges']:
			comment_range = CommentRange(
				comment = comment,
				start = ranges['start'],
				end = ranges['end'],
				startOffset = int(ranges['startOffset']),
				endOffset = int(ranges['endOffset']),
			)
			comment_range.save()
		response = HttpResponse(content="", status=303)
		response["Location"] = "/app/annotator_api/annotations/" + str(comment.id)
		return response

def api_search(request):
	""" Receives a search query and returns the annotations that match the 
		given search.
	"""
	submission_file_pk, user_pk = request.GET['uri'].split("+")
	submission_file = get_object_or_404(SubmissionFile, pk = submission_file_pk)
	user = get_object_or_404(User, pk = user_pk)
	comments = Comment.objects.filter(commenter=user, commented_file=submission_file)
	rows = [format_annotation(user, comment) for comment in comments]
	response = {'total':len(rows), 'rows':rows}
	return HttpResponse(json.dumps(response), content_type="application/json")

@csrf_exempt
def api_read(request, comment_pk):
	""" Receives the id of a Comment. It will then deal with that comment 
		according to the HTTP request type. PUT will update the comment,
		GET will return a JSON object of the comment, DELETE will remove that 
		comment from the database.
	"""
	comment = get_object_or_404(Comment, pk=comment_pk)
	if request.method == 'PUT':
		comment_data = json.loads(request.body)
		comment.comment = comment_data['text']
		comment.save()
		response = HttpResponse(content="", status=303)
		response["Location"] = "/app/annotator_api/annotations/" + str(comment.id)
		return response
	elif request.method == "DELETE":
		comment_ranges = CommentRange.objects.filter(comment=comment).delete()
		comment.delete()
		return HttpResponse(status=204)
	else:
		#TODO - Get actual user, this is just fake	
		user = User.objects.get(username='user1')
		response = format_annotation(user, comment)
		return HttpResponse(json.dumps(response), content_type="application/json")

def format_annotation(user, comment):
	""" Returns a comment in a format acceptable form AnnotatorJS. """
	#TODO - Might be missing some components need by AnnotatorJS
	comment_ranges = CommentRange.objects.filter(comment=comment)
	ranges = [{"start":r.start, "end":r.end, "startOffset":r.startOffset, "endOffset":r.endOffset} for r in comment_ranges]
	return {
		"id": comment.id,
		"text": comment.comment,
		"quote": comment.selected_text,
		"ranges": ranges,
		"user": user.id,
	}

def reset_test_database(request):
	now = timezone.now()
	just_before = timezone.now() - datetime.timedelta(seconds=10)
	before = timezone.now() - datetime.timedelta(days=1)
	long_before = timezone.now() - datetime.timedelta(days=30)
	just_after = timezone.now() + datetime.timedelta(seconds=10)
	after = timezone.now() + datetime.timedelta(days=1)
	long_after = timezone.now() + datetime.timedelta(days=30)
	user1 = User(username="user1")
	user1.save()
	user2 = User(username="user2")
	user2.save()
	user3 = User(username="user3")
	user3.save()
	user4 = User(username="user4")
	user4.save()
	course = Course(course_name="Test Course", course_code="TEST1000", course_id="201402TEST1000", year=2014, semester='2', institution="UQ")
	course.save()
	a1 = Assignment(
		assignment_id="ass01", 
		name="Assignment 1", 
		create_date=long_before, 
		modified_date=long_before, 
		open_date=long_before, 
		due_date=before, 
		description="This is assignment 1. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		allow_multiple_uploads=True,
		allow_help_centre=True,
		number_of_peer_reviews=3,
		review_open_date=just_after,
		review_due_date=after,
		weighting=20,
		has_tests=False,
		test_required=False
	)
	a1.save()
	a2 = Assignment(
		assignment_id="ass02", 
		name="Assignment 2", 
		create_date=before, 
		modified_date=before, 
		open_date=before, 
		due_date=after, 
		description="This is assignment 2. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		allow_multiple_uploads=True,
		allow_help_centre=True,
		number_of_peer_reviews=3,
		review_open_date=after,
		review_due_date=long_after,
		weighting=20,
		has_tests=False,
		test_required=False
	)
	a2.save()
	a3 = Assignment(
		assignment_id="ass03", 
		name="Assignment 3", 
		create_date=now, 
		modified_date=now, 
		open_date=after, 
		due_date=long_after, 
		description="This is assignment 3. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		allow_multiple_uploads=True,
		allow_help_centre=True,
		number_of_peer_reviews=3,
		review_open_date=long_after,
		review_due_date=long_after,
		weighting=20,
		has_tests=False,
		test_required=False
	)
	a3.save()

	## Prev assignment w/ review
	submission0 = Submission(
		user = user1,
		assignment = a1,
		upload_date = before,
		upload_path = "./test_submission/0/",
		has_been_submitted = True,
		unviewed_reviews = 1
	)
	submission0.save()

	sf0 = SubmissionFile(submission=submission0, file_path="test.py")
	sf0.save()
	assigned_review = AssignedReview(assigned_user=user2, assigned_submission=submission0, has_been_reviewed=True)
	assigned_review.save()
	comment = Comment(commenter=user2, commented_file=sf0, comment="Wow, much deep!", selected_text="print")
	comment.save()
	comment_range = CommentRange(comment=comment, start='', end='',startOffset=0, endOffset=5)
	comment_range.save()

	assigned_review2 = AssignedReview(assigned_user=user3, assigned_submission=submission0, has_been_reviewed=True)
	assigned_review2.save()
	comment2 = Comment(commenter=user3, commented_file=sf0, comment="Comment two", selected_text="print")
	comment2.save()
	comment_range2 = CommentRange(comment=comment2, start='', end='',startOffset=0, endOffset=5)
	comment_range2.save()

	submission1 = Submission(
		user = user2,
		assignment = a1,
		upload_date = just_before,
		upload_path = "./test_submission/1/",
		has_been_submitted = True,
		unviewed_reviews = 0
	)
	submission1.save()

	sf1 = SubmissionFile(submission=submission1, file_path="email.py")
	sf1.save()

	assigned_review3 = AssignedReview(assigned_user=user1, assigned_submission=submission1, has_been_reviewed=False)
	assigned_review3.save()

	submission2 = Submission(
		user = user3,
		assignment = a2,
		upload_date = just_before,
		upload_path = "./test_submission/2/",
		has_been_submitted = True,
		unviewed_reviews = 0
	)
	submission2.save()

	sf2 = SubmissionFile(submission=submission2, file_path="email.py")
	sf2.save()

	submission3 = Submission(
		user = user4,
		assignment = a2,
		upload_date = just_before,
		upload_path = "./test_submission/3/",
		has_been_submitted = True,
		unviewed_reviews = 0
	)
	submission3.save()

	sf3 = SubmissionFile(submission=submission3, file_path="email.py")
	sf3.save()

	return redirect('index')
