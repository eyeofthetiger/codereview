import requests
import json

def markdown_to_html(markdown):
	""" Converts text in Markdown format to HTML. """
	if len(markdown) > 0:
		return markdown_api(markdown)
	return markdown

def markdown_api(markdown):
	""" Makes a request to the Github API to convert text in Markdown format 
		to HTML. 
	"""
	payload = json.dumps({'text': markdown, 'mode': 'markdown', 'content':''})
	r = requests.post("https://api.github.com/markdown", data=payload)
	return r.content

