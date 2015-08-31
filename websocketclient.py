import websocket
import time


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



