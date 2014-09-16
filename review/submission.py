import os.path
from os import listdir
from zipfile import ZipFile, is_zipfile
import json

from django.utils import timezone
from django.http import HttpResponse

from review.models import SubmissionFile, Submission

""" This file contains all funcitons related to dealing with submissions and 
	storing them on the server.
"""

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