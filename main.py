import json
import os
from datetime import datetime

from flask import Flask, Response, render_template, request
from flask_cors import CORS

## CONFIG ##

template_file = 'index.html' # set to template to respond with when web browser is used.
# must be a .html file in the "templates" directory

MESSAGE_FILE = "messages.json" # set file to save message history to.
PORT = 81 # set port to run KFCR on.
HOST = "0.0.0.0" # set host to run KFCR on.
# 0.0.0.0 is public IP, 127.0.0.1 is local IP.

## CONFIG END ##



## ! PAST THIS POINT IS INTERNAL CODE ! ##
## ! DO NOT EDIT UNLESS YOU KNOW WHAT YOU ARE DOING, IT MIGHT BREAK ! ##
## ! SUPPORT/BUG REPORTS FROM SEVERLY EDITED CODE WILL **NOT** RECEIVE HELP ! ##

# if you know what you are doing, feel free to submit a pr.


# VERSION

KFCR_VERSION = 1
KFCR_RELEASE = "S" # A for alpha, B for beta, S for stable.
VERSION_FULL = KFCR_RELEASE + str(KFCR_VERSION)

# VERSION END

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    return render_template(template_file, version=VERSION_FULL)


@app.route('/KFCR_verification',  methods=['GET'])
def verify():
    return Response("KFCR verified!", status=200)

@app.route('/messages', methods=['GET', 'POST'])
def retrieve_history():
    if request.method == 'GET':
        # return the messages.json file as a json object
        try:
            with open(MESSAGE_FILE) as history:
                data = json.load(history)
                return Response(json.dumps(data), mimetype='application/json')
        except FileNotFoundError:
            return Response(f"designated message file '{MESSAGE_FILE}' does not exist", status=500)
        except json.JSONDecodeError:
            return Response("designated message file JSON decode error", status=500)

    elif request.method == 'POST':
        # append the message to the messages.json file
        data = request.get_json()
        with open(MESSAGE_FILE) as mh:
            message_history = json.load(mh)

        if data is None:
            return Response("Invalid JSON", status=400)

        if "content" in data and "user" in data:
            data["timestamp"] = str(datetime.now())
            message_history.append(data)

            with open(MESSAGE_FILE, 'w') as history:
                # append JSON object to MESSAGE_FILE
                json.dump(message_history, history)

            return Response('message successfully sent!', status=201)
        else:
            # return HTTP status code to indicate malformed input
            return Response("Malformed message JSON", status=400)


             
@app.route('/messages/latest', methods=['GET'])
def grab_latest_message():
    # return the last JSON object in the messages.json file
    # if the file is empty, return HTTP status code 404
    try:
        with open(MESSAGE_FILE) as history:
            # parse the entire file as JSON
            data = json.load(history)
            # get the last JSON object in the file
            last_object = data[-1]
            # return the last object as a JSON object
            return Response(json.dumps(last_object), mimetype='application/json')
    except (IndexError, json.JSONDecodeError):
        return Response("No messages found", status=404)



@app.route('/version', methods=['GET'])
def grab_version():
    return Response(VERSION_FULL, status=200)

@app.route('/version/release', methods=['GET'])
def release():
    return Response(KFCR_RELEASE, status=200)

@app.route('/version/number', methods=['GET'])
def number():
    return Response(str(KFCR_VERSION), status=200)



# Check if the JSON file is empty or not
if os.path.getsize(MESSAGE_FILE) <= 2:
    boot = [{"user": "KFCR", "content": "Booting KFCR", "timestamp": str(datetime.now())}]
    with open(MESSAGE_FILE, 'w') as bw:
        json.dump(boot, bw)

# run flask app
if __name__ == '__main__':
    app.run(host=HOST, port=PORT)