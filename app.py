import os, datetime
import random
import json

from flask import Flask, request, redirect, jsonify # Retrieve Flask, our framework
from flask import render_template

import pusher # Pusher.com python library
import requests # used to make calls to remote youtube api

app = Flask(__name__)   # create our flask app
app.config['CSRF_ENABLED'] = False


# configure pusher 
pusher.app_id = os.environ.get('PUSHER_APP_ID')
pusher.key = os.environ.get('PUSHER_KEY')
pusher.secret = os.environ.get('PUSHER_SECRET')
p = pusher.Pusher()
	

# this is our main page
@app.route("/")
def index():

	templateData = {
		'PUSHER_KEY' : os.environ.get('PUSHER_KEY')
	}
	return render_template("main.html", **templateData)


# ajax demo
@app.route('/ajax')
def ajax_demo():

	return render_template('ajax_demo.html')

# CHAT ROUTE
# GET --> renders push_chat.html
# POST --> accepts 'msg' form field and triggers PUSHER event
@app.route('/chat', methods=['GET','POST'])
def chat_demo():

	# received a POST request
	if request.method == 'POST':
		chatmsg = request.form.get('msg')
		
		if chatmsg:

			# send message for broadcast to pusher
			p['chat_demo'].trigger('incoming_chat',{'msg':chatmsg})

			# respond to ajax request
			return jsonify(status='OK',message='message sent:%s' % chatmsg)
			
		else:
			return jsonify(status='ERROR',message='no chatmsg was received')

	else:

		# GET request render template with pusher_key
		templateData = {
			'PUSHER_KEY' : os.environ.get('PUSHER_KEY')
		}
		return render_template('pusher_chat.html', **templateData)


@app.route("/couch", methods=['GET','POST'])
def pushit():

# received a POST request
	if request.method == 'POST':
		query = request.form.get('query')
		
		# query youtube
		videos = query_youtube_api(query)
		if videos:

			# Trigger PUSH message
			p['couch_potato'].trigger('incoming_youtube',{ 'video':videos[0] })

			# reply to POST request
			return jsonify(status='OK',message='query received:%s' % query)
		
	
		else:
			return jsonify(status='ERROR',message='no videos found.')

	else:

		# GET request render template with pusher_key
		templateData = {
			'PUSHER_KEY' : os.environ.get('PUSHER_KEY')
		}
		return render_template('pusher_couch.html', **templateData)



# /youtube_query POST route
# accepts 'query' field and searches youtube api v2.
# returns youtube as json
@app.route("/youtube_query",methods=['POST'])
def youtube_query():

	query = request.form.get('query')
	if query:

		videos = query_youtube_api(query)
			
		response_data = {
			'status' : 'OK',
			'videos' : videos
		}

	else:
		response_data = {
			'status' : 'error',
			'msg' : 'no query provided',

		}

	return jsonify(response_data)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


def query_youtube_api(query):
	# https://developers.google.com/youtube/2.0/developers_guide_json
	
	query_options = {
		'q':query,
		'order' : 'relevance',
		'alt' : 'json',
		'max-results' : '2'
	}
	youtube_api_url = 'https://gdata.youtube.com/feeds/api/videos'

	# make youtube api request
	yt_result = requests.get(youtube_api_url, params=query_options)
	
	# return yt_result.json()
	if yt_result.status_code == 200:
		data = yt_result.json()
		
		videos = data['feed']['entry']
		# we got some videos from the api
		# let's pull out the title and video id for each video
		if len(videos) > 0:

			video_info = []  # container for videos + information

			for v in videos:
				video_info.append({
					'title' : v['title']['$t'],
					'video_id' : v['id']['$t'].replace("http://gdata.youtube.com/feeds/api/videos/","")
				})
				
			return video_info
		else:
			return None
	else:
		return None


# start the webserver
if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)



	