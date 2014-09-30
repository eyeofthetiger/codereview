import os.path

import docker

def save_file(upload, directory):
	""" Receives an uploaded file, and a directory to place it in. Writes the
		uploaded file to the correct path. Returns the upload path.
	"""
	path = os.path.join(directory, upload.name)
	with open(path, "w") as f:
		f.write(upload.read())
	return path

def build_dockerfile(path):
	client = docker.Client(base_url='unix://var/run/docker.sock')
	return client.build(path=path)

def run_docker(image, testpath, command):
	client = docker.Client(base_url='unix://var/run/docker.sock')
	container = client.create_container(image, command=command)
	binds = { testpath: { 'bind': '/opt/testing', 'ro': False } }
	client.start(container, binds=binds)