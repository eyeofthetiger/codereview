""" This file contains function to be used in development. """
import datetime

from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import connections, transaction
from django.core.cache import cache # This is the memcache cache.

from review.models import Submission, SubmissionFile, Course, Assignment, \
	AssignedReview, Comment, CommentRange, EmailPreferences, Question, Response

@csrf_exempt
def choose_user(request):
	""" Loads the page for selecting a user. """
	return render(request, 'review/login.html')

def load_admin(request):
	""" Changes the user to account to be a staff member. """
	user = authenticate(username='admin', password='admin')
	login(request, user)
	return redirect('index')

def load_student(request):
	""" Changes the user to account to be a student. """
	user = authenticate(username='user1', password='user1')
	login(request, user)
	return redirect('index')

def reset_test_database(request):
	""" Loads a database with fake data for testing. """

	flush()

	# Delete current database
	Submission.objects.all().delete()
	SubmissionFile.objects.all().delete()
	Course.objects.all().delete()
	Assignment.objects.all().delete()
	AssignedReview.objects.all().delete()
	Comment.objects.all().delete()
	CommentRange.objects.all().delete()
	EmailPreferences.objects.all().delete()
	Question.objects.all().delete()
	Response.objects.all().delete()

	now = timezone.now()
	just_before = timezone.now() - datetime.timedelta(seconds=10)
	before = timezone.now() - datetime.timedelta(days=1)
	long_before = timezone.now() - datetime.timedelta(days=30)
	just_after = timezone.now() + datetime.timedelta(seconds=30)
	after = timezone.now() + datetime.timedelta(days=1)
	long_after = timezone.now() + datetime.timedelta(days=30)

	#Deal with users
	if len(User.objects.all()) <= 1:
		user1 = User(username="user1")
		user1.set_password('user1')
		user1.save()
		user2 = User(username="user2")
		user2.set_password('user2')
		user2.save()
		user3 = User(username="user3")
		user3.set_password('user3')
		user3.save()
		user4 = User(username="user4")
		user4.set_password('user4')
		user4.save()
	else:
		user1 = User.objects.filter(username="user1")[0]
		user2 = User.objects.filter(username="user2")[0]
		user3 = User.objects.filter(username="user3")[0]
		user4 = User.objects.filter(username="user4")[0]

	user1prefs = EmailPreferences(user=user1, on_day_before_due=True, on_due_date=True)
	user1prefs.save()
	
	user2prefs = EmailPreferences(user=user2)
	user2prefs.save()
	
	user3prefs = EmailPreferences(user=user3)
	user3prefs.save()
	
	user4prefs = EmailPreferences(user=user4)
	user4prefs.save()
	course = Course(course_name="Test Course", course_code="TEST1000", course_id="201402TEST1000", year=2014, semester='2', institution="UQ")
	course.save()
	a1 = Assignment(
		assignment_id="ass01", 
		name="Assignment 1", 
		create_date=long_before, 
		modified_date=long_before, 
		open_date=long_before, 
		due_date=just_before, 
		description="This is assignment 1. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		description_raw="This is assignment 1. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		allow_multiple_uploads=True,
		allow_help_centre=True,
		number_of_peer_reviews=3,
		review_open_date=just_before,
		review_due_date=after,
		weighting=20,
		has_tests=False,
		test_required=False
	)
	a1.save()
	a1.set_async()
	print "a1 created"
	a2 = Assignment(
		assignment_id="ass02", 
		name="Assignment 2", 
		create_date=before, 
		modified_date=before, 
		open_date=before, 
		due_date=just_after, 
		description="This is assignment 2. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		description_raw="This is assignment 2. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		allow_multiple_uploads=True,
		allow_help_centre=True,
		number_of_peer_reviews=3,
		review_open_date=just_after,
		review_due_date=long_after,
		weighting=20,
		has_tests=False,
		test_required=False
	)
	a2.save()
	a2.set_async()
	print "a2 created"
	a3 = Assignment(
		assignment_id="ass03", 
		name="Assignment 3", 
		create_date=now, 
		modified_date=now, 
		open_date=just_after, 
		due_date=long_after, 
		description="This is assignment 3. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
		description_raw="This is assignment 3. Bacon ipsum dolor sit amet short loin jowl swine, drumstick hamburger meatball prosciutto frankfurter chuck. Shank sausage doner meatball shankle flank, t-bone venison turkey jerky bacon strip steak ribeye chicken pastrami. Capicola ground round corned beef turducken frankfurter. Jowl landjaeger bacon, sausage frankfurter meatball rump bresaola strip steak fatback short loin jerky pancetta turducken.",
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
	a3.set_async()
	print "a3 created"
	## Prev assignment w/ review
	submission0 = Submission(
		user = user1,
		assignment = a1,
		upload_date = before,
		upload_path = "codereview/test_submission/0/",
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
		assignment = a2,
		upload_date = just_before,
		upload_path = "codereview/test_submission/1/",
		has_been_submitted = True,
		unviewed_reviews = 0
	)
	submission1.save()

	sf1 = SubmissionFile(submission=submission1, file_path="email.py")
	sf1.save()
	submission2 = Submission(
		user = user3,
		assignment = a2,
		upload_date = just_before,
		upload_path = "codereview/test_submission/2/",
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
		upload_path = "codereview/test_submission/3/",
		has_been_submitted = True,
		unviewed_reviews = 0
	)
	submission3.save()

	sf3 = SubmissionFile(submission=submission3, file_path="email.py")
	sf3.save()

	question1 = Question(
		user = user4,
		title = "Why is the sky blue?",
		text = "Tell me why.",
		text_raw = "Tell me why.",
		create_date = long_before,
		modified_date = just_before,
	)
	question1.save()

	question2 = Question(
		user = user4,
		title = "Why did the chicken cross the road?",
		text = "Bacon ipsum dolor sit amet short loin jowl swine.",
		text_raw = "Bacon ipsum dolor sit amet short loin jowl swine.",
		create_date = long_before,
		modified_date = long_before,
	)
	question2.save()

	answer1 = Response(
		user = user2,
		question = question2,
		text = "Just because.",
		text_raw = "Just because.",
		create_date = before,
		modified_date = before,
	)
	answer1.save()

	answer2 = Response(
		user = user2,
		question = question2,
		text = "Egg.",
		text_raw = "Egg.",
		create_date = before,
		modified_date = before,
	)
	answer2.save()

	return redirect('index')


def flush():
    # This works as advertised on the memcached cache:
    cache.clear()
    # This manually purges the SQLite cache:
    cursor = connections['cache_database'].cursor()
    cursor.execute('DELETE FROM cache_table')
    transaction.commit_unless_managed(using='cache_database')