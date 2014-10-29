import os.path
from subprocess import Popen, PIPE, call
import random
import string
from zipfile import ZipFile, is_zipfile

def save_file(upload, directory):
	""" Receives an uploaded file, and a directory to place it in. Writes the
		uploaded file to the correct path. Returns the upload path.
	"""
	path = os.path.join(directory, upload.name)
	with open(path, "w") as f:
		f.write(upload.read())
	return path

def build_dockerfile(path, assignment_id):
	""" Builds a docker instance from the given Dockerfile. """
	call(['sudo', 'docker', 'build', '-t', 'enkidu/' + str(assignment_id), 
		path])

def run_docker(assignment_id, testpath, command):
	""" Runs a docker instance with the given command. """
	cmd = 'sudo docker run -t -a stdout -v ' + testpath + ":/opt/testing" + \
		' enkidu/' + str(assignment_id) + ' ' + command
	print cmd
	# Hacky workaround of writing to shell file because pytohn thinks the mount 
	# volume for Docker is acutally a local dir
	sh_file = os.path.join(testpath, 'docker.sh')
	with open(sh_file, 'w') as f:
		f.write(cmd)
	p = Popen(['timeout', '-s', 'SIGKILL', '2', 'sh', sh_file], stdout=PIPE)
	output, err = p.communicate()
	
	# Append Docker output to stdout
	output_file = os.path.join(testpath, 'output.txt')
	if os.path.isfile(output_file):
		with open(output_file, 'r') as f:
			for line in f.readlines():
				output += line
	return output

def create_temp_files(assignment, submission_file):
	""" Puts a submission and the testing files into the same directory. """
	# Create enclosing folder
	directory = generate_random_name()
	# Might get stuck if run over 200 billion times
	while os.path.isdir(os.path.join('temp', 'testing', directory)):
		directory = generate_random_name()
	path = os.path.join('temp', 'testing', directory)
	os.makedirs(path)

	# Copy test files
	with ZipFile(assignment.test_zip, 'r') as zip_object:
		for f in zip_object.namelist():
			zip_object.extract(f, path=path)

	# Copy submission files
	if is_zipfile(submission_file):
		with ZipFile(submission_file, 'r') as zip_object:
			for f in zip_object.namelist():
				zip_object.extract(f, path=path)
	else:
		temp_file = os.path.join(path, submission_file.name)
		submission_file.seek(0) # Reset cursor
		with open(temp_file, 'w') as f:
			f.write(submission_file.read())
	return path


def generate_random_name():
	""" Generates a random string of 8 chars. """
	alpha = string.ascii_lowercase
	return ''.join(random.sample(alpha,len(alpha)))[:8]