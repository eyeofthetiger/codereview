import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from review.models import Comment, CommentRange, SubmissionFile, Submission, AssignedReview

""" Functions related to annotation. """

def api_root(request):
	""" Returns information about the annotator API. """
	response = { "name": "Annotator Store API", "version": "2.0.0" }
	return HttpResponse(json.dumps(response), content_type="application/json")

@csrf_exempt
def api_index(request):
	""" If request type is GET, returns 404. If request 
		type is POST, stores posted annotation.
	"""
	if request.method == 'POST':
		#Save comment
		comment_data = json.loads(request.body)
		submission_file_pk, user_pk = comment_data['uri'].split("+")
		submission_file = get_object_or_404(
			SubmissionFile, pk = submission_file_pk)
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
		response["Location"] = "/app/annotator_api/annotations/" + \
			str(comment.id)
		return response
	else:
		return HttpResponse(status=404)

def api_search(request):
	""" Receives a search query and returns the annotations that match the 
		given search.
	"""
	submission_file_pk, user_pk = request.GET['uri'].split("+")
	submission_file = get_object_or_404(SubmissionFile, pk = submission_file_pk)
	user = get_object_or_404(User, pk = user_pk)
	comments = Comment.objects.filter(
		commenter=user, commented_file=submission_file)
	rows = [format_annotation(user, comment) for comment in comments]
	response = {'total':len(rows), 'rows':rows}
	return HttpResponse(json.dumps(response), content_type="application/json")

@csrf_exempt
def api_delete_all(request, submission_file_pk, user_pk):
	""" Receives SubmissionFile and User primary keys and deletes all comments
		made by that user on that file.
	"""
	submission_file = get_object_or_404(SubmissionFile, pk=submission_file_pk)
	user = get_object_or_404(User, pk = user_pk)
	comments = Comment.objects.filter(
		commenter=user, commented_file=submission_file)
	for comment in comments:
		comment_ranges = CommentRange.objects.filter(comment=comment).delete()
		comment.delete()
	return HttpResponse(status=204)


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
		user = request.user
		response = format_annotation(user, comment)
		return HttpResponse(json.dumps(response),
			content_type="application/json")

@csrf_exempt
def submit_review(request, user_pk, submission_pk):
	""" Sets the given AssignedReview as complete and notifies the reviewed 
		user if necesssary.
	"""

	submission = get_object_or_404(Submission, pk=submission_pk)
	user = get_object_or_404(User, pk=user_pk)
	# Get review. There should only ever be one matching this input.
	review = AssignedReview.objects.filter(
		assigned_user=user, assigned_submission=submission)[0]
	review.has_been_reviewed = True
	review.save()
	print review
	return HttpResponse(status=204)

def format_annotation(user, comment):
	""" Returns a comment in a format acceptable form AnnotatorJS. """
	#TODO - Might be missing some components need by AnnotatorJS
	comment_ranges = CommentRange.objects.filter(comment=comment)
	ranges = [
		{
			"start":r.start, 
			"end":r.end, 
			"startOffset":r.startOffset, 
			"endOffset":r.endOffset
		} for r in comment_ranges]
	return {
		"id": comment.id,
		"text": comment.comment,
		"quote": comment.selected_text,
		"ranges": ranges,
		"user": user.id,
	}