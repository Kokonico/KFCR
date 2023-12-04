import copy
import json
import os
import sqlite3
import time

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

## CONFIG ##

template_file = 'index.html'  # set the page to respond with when web browser is used
# must be a .html file in the "templates" directory

DB_FILE = "messages.db"  # set file to save message history to.
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
KFCR_BRANCH = "SQLite test branch"  # branch of version
VERSION_FULL = KFCR_RELEASE + str(KFCR_VERSION) + f" ({KFCR_BRANCH})"

# VERSION END

# IMPORTANT EXEC

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
id INTEGER PRIMARY KEY,
user TEXT NOT NULL,
content TEXT NOT NULL,
timestamp INTEGER NOT NULL,
sys BOOLEAN NOT NULL);
""")

conn.commit()
conn.close()


## FUNCTIONS


def now():
  """get unix time"""
  return time.time_ns() // 1_000_000


def get_db():
  conn = sqlite3.connect(DB_FILE, check_same_thread=False)
  cursor = conn.cursor()
  return conn, cursor


def store(data):
  conn, cursor = get_db()

  try:
    sqlmessage = (str(data["user"]), str(data["content"]), int(data["timestamp"]), bool(data["sys"]))
  except KeyError:
    raise ValueError("Missing required data.") from KeyError
  except ValueError:
    raise ValueError("Invalid data.") from ValueError
  
  cursor.execute(
      """
        INSERT INTO messages (user, content, timestamp, sys)
        VALUES (?, ?, ?, ?)
        """, sqlmessage)
  conn.commit()
  conn.close()

def convert_dict(tuple_list):
  messages = []
  for row in tuple_list:
    # convert sys to boolean from 1/0 state
    truesys = None
    if row[4] == 1:
      truesys = True
    elif row[4] == 0:
      truesys = False
    # convert tuple to message dict
    message = {
      "id": row[0],
      "user": row[1],
      "content": row[2],
      "timestamp": row[3],
      "sys": truesys
    }
    messages.append(message)
  return messages


## FUNCTIONS END

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
      store(data)
    except ValueError:
      return Response("Invalid JSON", status=400)

    return Response('message successfully sent!', status=201)
  else:
    # return HTTP status code to indicate malformed input
    return Response("Malformed message JSON", status=400)


@app.route('/messages/last/<path:msg_num>', methods=['GET'])
def load_history(msg_num):
  try:
    msg_int = int(msg_num)
  except ValueError:
    return Response("Invalid message number", status=400)

  conn, cursor = get_db()

  cursor.execute("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (msg_int, ))

  rows = cursor.fetchall()

  conn.commit()
  conn.close()

  return jsonify(convert_dict(rows))


@app.route('/messages/since/<path:unixstamp>', methods=['GET'])
def get_messages_since(unixstamp):
  # get all messages since unix timestamp from SQLite
  # if the timestamp is invalid, return HTTP status code 400

  conn, cursor = get_db()
  
  try:
    unixstamp_int = int(unixstamp)
  except ValueError:
    return Response("Bad timestamp", status=400)

  # get all messages since unix timestamp from SQLite
  cursor.execute("SELECT * FROM messages WHERE timestamp >= ?",
                 (unixstamp_int, ))

  # return the messages as a JSON object
  rows = cursor.fetchall()

  return jsonify(convert_dict(rows))


@app.route('/messages/id/<path:msgid>', methods=['GET'])
def get_id(msgid):
  # get message of id from SQLite
  # if the id is invalid, return HTTP status code 400
  # if the id does not exist, return 404.
  # if the id exists, return the message as a JSON object
  conn, cursor = get_db()
  
  try:
    msgid_int = int(msgid)
  except ValueError:
    return Response("invalid id", status=400)
  
  cursor.execute("SELECT * FROM messages WHERE id = ?", (msgid_int, ))
  
  rows = cursor.fetchall()

  try:
    result = jsonify(convert_dict(rows)[0])
  except IndexError:
    return Response(f'no message with id "{msgid}"', status=404)
  
  return result
  


@app.route('/messages/sinceid/<path:mid>')
def retrievesince(mid):
  if isinstance(mid, int):
      conn, cursor = get_db()
      cursor.execute("SELECT * FROM messages WHERE id > ?", (mid, ))
      rows = cursor.fetchall()

      conn.commit()
      conn.close()
    
      messages = []
      for row in rows:
        # convert sys to boolean from 1/0 state
        truesys = None
        if row[4] == 1:
          truesys = True
        elif row[4] == 0:
          truesys = False
        # convert tuple to message dict
        message = {
          "id": row[0],
          "user": row[1],
          "content": row[2],
          "timestamp": row[3],
          "sys": truesys
        }
        messages.append(message)

  return jsonify(messages)
      
  else:
      return Response('invalid message ID')

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

@app.route('/version/branch', methods=['GET'])
def branch():
  return Response(KFCR_BRANCH, status=200)

# EXEC

# check if the DB file contains no messages
boot = {
    "user": "KFCR",
    "content": "Booting KFCR",
    "timestamp": now(),
    "sys": True
}
store(boot)


# run flask app
if __name__ == '__main__':
  app.run(host=HOST, port=PORT)
