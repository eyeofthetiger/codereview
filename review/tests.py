from datetime import timedelta
import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.urlresolvers import reverse, resolve
from django.core.files import File

from codereview.wsgi import *
from review.allocation import swap_with_other_student
from review.annotator import api_root, api_index, api_search, api_read,\
	format_annotation
from review.email import send_email
from review.models import Course, Assignment, Submission, SubmissionFile, \
	Question, Comment, CommentRange
from review.markdown import markdown_to_html, markdown_api
from review.templatetags.template_tags import get_item, get_range, \
	get_submission_date, get_submission_id
from review.forms import UploadForm, QuestionForm, ResponseForm, \
	EmailPreferencesForm, AssignmentForm
from review.submission import is_valid_file, get_file_contents, \
	get_directory_contents

############################
# ALLOCATION TESTS
############################

class AllocationTest(TestCase):

	def test_allocation(self):
		pass

############################
# ANNOTATOR TESTS
############################

class AnnotatorTest(TestCase):

	def test_annotator(self):
		u = User.objects.create()
		t = timezone.now()
		a = Assignment.objects.create(
			assignment_id = "id",
			name = "name",
			create_date = t,
			modified_date = t,
			open_date = t,
			due_date = t,
			description = "description",
			description_raw = "description",
			allow_multiple_uploads = True,
			allow_help_centre = True,
			number_of_peer_reviews = 3,
			review_open_date = t,
			review_due_date = t,
			weighting = 10,
			test_zip = "test",
			dockerfile = "test",
			docker_command = "test",
			test_required = False,
		)
		s = Submission.objects.create(
			user = u,
			assignment = a,
			upload_date = t,
			upload_path = "test",
			has_been_submitted = True,
			unviewed_reviews = 0,
		)
		sf = SubmissionFile.objects.create(
			submission = s,
			file_path = "test"
		)
		c = Comment.objects.create(
			commenter=u, 
			commented_file=sf, 
			comment='test',
			selected_text='test',
		)
		cr = CommentRange.objects.create(
			comment=c, 
			start='test', 
			end='test',
			startOffset=0,
			endOffset=3,
		)
		expected = {
			"id": c.id,
			"text": c.comment,
			"quote": c.selected_text,
			"ranges": [{
				"start":cr.start,
				"end":cr.end, 
				"startOffset":cr.startOffset, 
				"endOffset":cr.endOffset
			}],
			"user": u.id,
		}
		self.assertEquals(format_annotation(u, c), expected)

		# Test API root
		url = reverse("review.annotator.api_root")
		resp = self.client.get(url)
		self.assertEquals(resp.status_code, 200)
		expected = '{"version": "2.0.0", "name": "Annotator Store API"}'
		self.assertEquals(resp.content, expected )

		# Test API index
		url = reverse("review.annotator.api_index")
		resp = self.client.get(url)
		self.assertEquals(resp.status_code, 404)
		post = {
			'uri': str(sf.id) + "+" + str(u.id),
			'quote': 'test',
			'text': 'test',
			'ranges':[]
		}
		resp = self.client.post(url, content_type='application/json', 
			data=json.dumps(post))
		self.assertEquals(resp.status_code, 303)
		self.assertEquals(resp.content, '')
		expected = "http://testserver/app/annotator_api/annotations/2"
		self.assertEquals(resp["Location"], expected)

############################
# EMAIL TESTS
############################

class EmailTest(TestCase):
	def test_email(self):
		self.assertEquals(send_email("test","test",['hello@world.com']), None)

############################
# FORMS TESTS
############################

class UploadFormTest(TestCase):

	# def test_valid(self):
	# 	data = {'file':File(None)}
	# 	form = UploadForm(data=data)
	# 	self.assertTrue(form.is_valid())

	def test_invalid(self):
		data = {'file':None}
		form = UploadForm(data=data)
		self.assertFalse(form.is_valid())

class QuestionFormTest(TestCase):

	def test_valid(self):
		u = User.objects.create()
		q = Question.objects.create(
			user=u, 
			title='test', 
			text='test',
			text_raw='test',
			create_date=timezone.now(),
			modified_date=timezone.now(),
			stickied=False,
		)
		data = {"title":q.title, "text_raw":q.text_raw}
		form = QuestionForm(data=data)
		self.assertTrue(form.is_valid())

	def test_invalid(self):
		u = User.objects.create()
		q = Question.objects.create(
			user=u, 
			title='', 
			text='test',
			text_raw='test',
			create_date=timezone.now(),
			modified_date=timezone.now(),
			stickied=False,
		)
		data = {"title":q.title, "text_raw":q.text_raw}
		form = QuestionForm(data=data)
		self.assertFalse(form.is_valid())

############################
# MARKDOWN TESTS
############################

class MarkdownTest(TestCase):

	def test_markdown(self):
		self.assertEquals(markdown_to_html(""), "")
		self.assertEquals(markdown_to_html("hi"), "<p>hi</p>\n")
		self.assertEquals(markdown_api("_hi_"), "<p><em>hi</em></p>\n")

############################
# MODELS TESTS
############################

class CourseTest(TestCase):

	def create_course(self):
		return Course.objects.create(
			course_name = "test",
			course_code = "test",
			course_id = "test",
			year = 2000,
			semester = "test",
			institution = "test",
		)

	def test_course_creation(self):
		obj = self.create_course()
		self.assertTrue(isinstance(obj, Course))
		self.assertEqual(obj.__unicode__(), "test - test")

class AssignmentTest(TestCase):

	def create_assignment(self, date):
		return Assignment.objects.create(
			assignment_id = "id",
			name = "name",
			create_date = date,
			modified_date = date,
			open_date = date,
			due_date = date,
			description = "description",
			description_raw = "description",
			allow_multiple_uploads = True,
			allow_help_centre = True,
			number_of_peer_reviews = 3,
			review_open_date = date,
			review_due_date = date,
			weighting = 10,
			test_zip = "test",
			dockerfile = "test",
			docker_command = "test",
			test_required = False,
		)

	def test_assignment_creation(self):
		t = timezone.now()
		obj = self.create_assignment(t)
		self.assertTrue(isinstance(obj, Assignment))
		self.assertEqual(obj.__unicode__(), obj.name)
		self.assertTrue(obj.has_tests())
		self.assertTrue(obj.due_date_passed())
		#Test database so no submissions
		self.assertEqual(obj.get_submission(None), None)
		# Async can't be tested, should return None either way
		self.assertEqual(obj.set_async(), None)
		self.assertEqual(obj.get_before_due_date(), t - timedelta(days=1))

class SubmissionTest(TestCase):

	def create_submission(self):
		t = timezone.now()
		u = User.objects.create()
		a = Assignment.objects.create(
			assignment_id = "id",
			name = "name",
			create_date = t,
			modified_date = t,
			open_date = t,
			due_date = t,
			description = "description",
			description_raw = "description",
			allow_multiple_uploads = True,
			allow_help_centre = True,
			number_of_peer_reviews = 3,
			review_open_date = t,
			review_due_date = t,
			weighting = 10,
			test_zip = "test",
			dockerfile = "test",
			docker_command = "test",
			test_required = False,
		)
		return Submission.objects.create(
			user = u,
			assignment = a,
			upload_date = t,
			upload_path = "test",
			has_been_submitted = True,
			unviewed_reviews = 0,
		)

	def test_submission_creation(self):
		obj = self.create_submission()
		self.assertTrue(isinstance(obj, Submission))
		self.assertEqual(obj.__unicode__(), str(obj.id))

class SubmissionFileTest(TestCase):

	def create_submission_file(self):
		t = timezone.now()
		u = User.objects.create()
		a = Assignment.objects.create(
			assignment_id = "id",
			name = "name",
			create_date = t,
			modified_date = t,
			open_date = t,
			due_date = t,
			description = "description",
			description_raw = "description",
			allow_multiple_uploads = True,
			allow_help_centre = True,
			number_of_peer_reviews = 3,
			review_open_date = t,
			review_due_date = t,
			weighting = 10,
			test_zip = "test",
			dockerfile = "test",
			docker_command = "test",
			test_required = False,
		)
		s = Submission.objects.create(
			user = u,
			assignment = a,
			upload_date = t,
			upload_path = "test",
			has_been_submitted = True,
			unviewed_reviews = 0,
		)
		return SubmissionFile.objects.create(
			submission = s,
			file_path = "test"
		)


	def test_submission_file_creation(self):
		obj = self.create_submission_file()
		self.assertTrue(isinstance(obj, SubmissionFile))
		self.assertEqual(obj.__unicode__(), "test")

############################
# SUBMISSION TESTS
############################

class SubmissionTest(TestCase):

	def test_is_valid_file(self):
		self.assertTrue(is_valid_file("tests.py"))
		self.assertFalse(is_valid_file("tests.pyc"))

	def test_get_file_contents(self):
		self.assertEquals(get_file_contents("review/__init__.py"),
		 "# This comment is for testing\n")

	def test_get_directory_contents(self):
		self.assertEquals(get_directory_contents("review/templatetags"), [
			{
				'icon': False, 
				'id': '__init__.py', 
				'parent': '#', 
				'text': '__init__.py'
			}, 
			{
				'icon': False, 
				'id': 'template_tags.py', 
				'parent': '#', 
				'text': 'template_tags.py'
			}
		])

############################
# TEMPLATE TAGS TESTS
############################
class S(object):
	# Mock submission for testing
	def __init__(self):
		self.upload_date = True
		self.id = True

class TemplateTagsTest(TestCase):

	def test_template_tags(self):
		self.assertTrue(get_item({'test':True}, 'test'))
		self.assertEquals(get_range([1,2,3]), [1,2,3])

		self.assertTrue(get_submission_date({'s':S()}, 's'))
		self.assertTrue(get_submission_id({'s':S()}, 's'))
		self.assertEquals(get_submission_date({}, 'test'), None)
		self.assertEquals(get_submission_id({}, 'test'), None)
