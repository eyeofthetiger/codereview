import requests
import json

def markdown_to_html(markdown):
	if len(markdown) > 0:
		return markdown_api(markdown)
	return markdown

def markdown_api(markdown):
	payload = json.dumps({'text': markdown, 'mode': 'markdown', 'content':''})
	r = requests.post("https://api.github.com/markdown", data=payload)
	return r.content

