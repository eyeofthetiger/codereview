import json

from flask import Flask, render_template, request
from mpd import MPDClient

import commands

app = Flask(__name__)

mpd_client = MPDClient(use_unicode=True)
mpd_client.timeout = 10
mpd_client.connect("192.168.1.4", 6600)

@app.route("/")
def index():
	return render_template('index.html')

@app.route("/command", methods=['POST'])
def command():
	json_data = json.loads(request.data)
	command = json_data['command']
	print "Command: " + command
	parse_command(command)
	return render_template('index.html')

def parse_command(text):
	if text == "play":
		commands.play(mpd_client)
	elif text == "stop":
		commands.stop(mpd_client)
	elif text.startswith("play some "):
		commands.play_some(mpd_client, text[10:])

if __name__ == "__main__":
	app.debug = True
	app.run()