import os.path
from subprocess import call

# import docker

def save_file(upload, directory):
	""" Receives an uploaded file, and a directory to place it in. Writes the
		uploaded file to the correct path. Returns the upload path.
	"""
	path = os.path.join(directory, upload.name)
	with open(path, "w") as f:
		f.write(upload.read())
	return path

def build_dockerfile(path, assignment_id):
	call(['sudo', 'docker', 'build', '-t', 'enkidu/' + str(assignment_id), path])

def run_docker(assignment_id, testpath, command):
	call([
		'sudo', 
		'docker', 
		'run', 
		'-v', 
		testpath + ":/opt/testing", 
		'enkidu/' + str(assignment_id),
		command
	])