import copy
import json
import os
import sqlite3
import time

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

## CONFIG ##

template_file = 'index.html'  # set to template to respond with when web browser is used.
# must be a .html file in the "templates" directory

DB_FILE = "messages.db"  # set file to save message history to.
MESSAGE_FILE = "messages.json"
PORT = 81  # set port to run KFCR on.
HOST = "0.0.0.0"  # set host to run KFCR on.
# 0.0.0.0 is public IP, 127.0.0.1 is local IP.

## CONFIG END ##




## ! PAST THIS POINT IS INTERNAL CODE ! ##
## ! DO NOT EDIT UNLESS YOU KNOW WHAT YOU ARE DOING, IT MIGHT BREAK ! ##
## ! SUPPORT/BUG REPORTS FROM SEVERLY EDITED CODE WILL **NOT** RECEIVE HELP ! ##

# if you know what you are doing, feel free to edit or submit a pr.

# VERSION

KFCR_VERSION = 3
KFCR_RELEASE = "A"  # A for alpha, B for beta, S for stable.
VERSION_FULL = KFCR_RELEASE + str(KFCR_VERSION)

# VERSION END

# IMPORTANT EXEC

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
id INTEGER PRIMARY KEY,
user TEXT NOT NULL,
content TEXT NOT NULL,
timestamp INTEGER NOT NULL,
sys BOOLEAN NOT NULL);
""")


def now():
  return time.time_ns() // 1_000_000


def check_json(json_obj, disallow):
  if isinstance(json_obj, dict):
    for key, value in json_obj.items():
      if any(char in str(value) for char in disallow):
        return False
      if not check_json(value, disallow):
        return False
  elif isinstance(json_obj, list):
    for item in json_obj:
      if not check_json(item, disallow):
        return False
  return True


def stripped(json_obj, expected_keys):
  if isinstance(json_obj, dict):
    stripped_obj = copy.deepcopy(json_obj)
    keys_to_remove = [key for key in stripped_obj if key not in expected_keys]
    for key in keys_to_remove:
      del stripped_obj[key]
    for key, value in stripped_obj.items():
      stripped_obj[key] = stripped(value, expected_keys)
    return stripped_obj
  elif isinstance(json_obj, list):
    return [stripped(item, expected_keys) for item in json_obj]
  else:
    return json_obj  # I love overengineering


app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def index():
  return render_template(template_file, version=VERSION_FULL)


@app.route('/KFCR_verification', methods=['GET'])
def verify():
  return Response("KFCR verified!", status=200)


## MAIN ##

@app.route('/messages/post', methods=['POST'])
def post_message():
  # append the message to the messages.json file
  data = request.get_json()

  if data is None:
    return Response("Invalid JSON", status=400)

  if "content" in data and "user" in data:

    data["timestamp"] = now()
    data["sys"] = False
    try:
      sqlmessage = (str(data["user"]), str(data["content"]),
                    int(data["timestamp"]), bool(data["sys"]))
    except ValueError:
      return Response("Invalid JSON", status=400)

    cursor.execute(
      """
      INSERT INTO messages(user, content, timestamp, sys)
      VALUES(?, ?, ?, ?)
      """, (sqlmessage, ))

    return Response('message successfully sent!', status=201)
  else:
    # return HTTP status code to indicate malformed input
    return Response("Malformed message JSON", status=400)




@app.route('messages/last/<path:msg_num>', methods=['GET'])
def load_history(msg_num):
  # return the last <msg_num> messages
  try:
    msg_int = int(msg_num)
  except ValueError:
    return Response("Invalid message number", status=400)

  # return last <msg_num> messages from SQLite
  cursor.execute("SELECT * FROM messages WHERE id >= ?", (msg_int, ))

  rows = cursor.fetchall()

  messages = []
  for row in rows:
    message = dict(row)
    messages.append(message)

  return jsonify(messages)




@app.route('/messages/since/<path:unixstamp>', methods=['GET'])
def get_messages_since(unixstamp):
  # get all messages since unix timestamp from SQLite
  # if the timestamp is invalid, return HTTP status code 400
  try:
    unixstamp_int = int(unixstamp)
  except ValueError:
    return Response("Bad timestamp", status=400)

  # get all messages since unix timestamp from SQLite
  cursor.execute("SELECT * FROM messages WHERE timestamp >= ?", (unixstamp_int, ))

  # return the messages as a JSON object
  rows = cursor.fetchall()

  messages = []
  for row in rows:
    message = dict(row)
    messages.append(message)

  return jsonify(messages)

## MAIN END


@app.route('/version', methods=['GET'])
def grab_version():
  return Response(VERSION_FULL, status=200)


@app.route('/version/release', methods=['GET'])
def release():
  return Response(KFCR_RELEASE, status=200)


@app.route('/version/number', methods=['GET'])
def number():
  return Response(str(KFCR_VERSION), status=200)


# EXEC

# Check if the JSON file is empty or not
if os.path.getsize(MESSAGE_FILE) <= 2:
  boot = [{
      "user": "KFCR",
      "content": "Booting KFCR",
      "timestamp": now(),
      "sys": True
  }]
  with open(MESSAGE_FILE, 'w') as bw:
    json.dump(boot, bw)

# run flask app
if __name__ == '__main__':
  app.run(host=HOST, port=PORT)
