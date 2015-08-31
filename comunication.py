import websocket
import time
import requests
import json
from collections import deque

transactions = deque()

def on_message(ws, message):
	message_to_server = "pong"
	print message
	ws.send(message_to_server)
	print (message_to_server+"\n")


def on_error(ws, error):
	print error

def on_close(ws):
	print "### closed ###"

def on_open(ws):
	print "### open ###"

def websockets():
	websocket.enableTrace(False)
	ws = websocket.WebSocketApp("ws://192.168.1.15:3000/",
	on_message = on_message,
	on_error = on_error,
	on_close = on_close)
	ws.on_open = on_open
	ws.run_forever()

def send_transaction(tag_id , direction):
	time = int(time.time())

	url = "http://192.168.1.15:3000/api/portal_endpoint/transaction/1"
	data = '{"tagId":'+ str(tag_id) +',"direction":"'+direction+'","time":'+str(time)+'}'
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
	print json.dumps(data)
	try:
		r = requests.post(url, data, headers=headers)
	except:
		
		transactions.append(data)

	if not transactions :
			while not transactions:
				r = requests.post(url, data=transactions.pop(), headers=headers)


