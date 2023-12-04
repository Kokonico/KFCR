# WARNING

this is the ***highly unstable*** and ***insecure*** JSON branch. It only exists for ***Archiving purposes***. please **DO NOT** use in prod!

# KFCR

## a simple chat server written in flask

kfcr is an easily customisable chat server that uses HTTP requests in order to communicate.

# basic rundown (for building clients)

to verify a url is indeed, a KFCR server, send a GET request to "url/KFCR_verification"

this will return a 200 if it's a kfcr server, it will most likely be a 404 elsewhere.
to be extra sure, it also returns the text "KFCR verified!"


each message is a JSON object consisting of three keys

{
  "user": "jimbob"
  "content": "hello world!"
  "timestamp": time server received and proccessed message, is in the format of running "datetime.now()"
}

to call for every message ever sent. make a GET request to "url/messages"

to call for the latest message ever sent, make a GET request to "url/messages/latest"

to POST a message successfully, you must make a POST request to "url/messages", and send a JSON object with two keys, "user", and "content"
"user" is the username to be stored, and "content" is the text of the message. ex:

{
  "user": "jimbob",
  "content": "foo"
}

there are no sockets in KFCR. good luck ;)

## version checking

to get the full version id, send a GET request to "url/version"

to get the release channel of the KFCR instance on the server, send a GET request to "url/version/release".
this should return text that is either "A", alpha, "B", beta, "S", stable, or "D", deprecated.

to get the version number of the KFCR instance, send a GET request to "url/version/number".

this is all to it. good luck ;)
