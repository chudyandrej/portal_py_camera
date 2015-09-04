import websocket
import requests
import json
import time
import os
import pygame
#### Configuring Settings ####
server_url = "192.168.1.14"
portalID = "1"
##############################
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
	ws = websocket.WebSocketApp("ws://"+server_url+"/",
	on_message = on_message,
	on_error = on_error,
	on_close = on_close)
	ws.on_open = on_open
	ws.run_forever()

def send_transaction(tag_id , direction):
	after_disconect = False				
	url = "http://"+server_url+"/api/portal_endpoint/transaction/"+portalID+""
	data = '{"tagId":'+str(tag_id)+',"direction":"'+direction+'","time":'+str(int(time.time()))+'}'
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
	
	try:
		r = requests.post(url, data, headers)	#try send transaction
		if os.stat("transaction_backup.txt").st_size != 0:	#if existing some old transaction
			trans_backup =  open("transaction_backup.txt") 	
			for line in trans_backup:			#send all old transaction
				r = requests.post(url, line, headers)	
			trans_backup.close()
			open('transaction_backup.txt', 'w').close()	#delete transactions
		
	except:
		print '\033[1;31mServer not reachable\033[1;m'
		target = open("transaction_backup.txt", 'a')	
		target.write(data+"\n")
		target.close()
		after_disconect = False

def get_request(url):

	try: 
		r = requests.get(url)	#try get request

	except:
		
		print '\033[1;31m Server not reachable \033[1;m'
		return None ,None
	json_request = json.loads(r.text)	#convert to json
	return json_request , r.text	

def get_json_config():
	settings, text = get_request("http://"+server_url+"/api/portal_endpoint/settings/"+portalID+"")
	if settings != None:	#if server is ok
		file_set = open("settings.txt", 'w')
		file_set.write(text)
		file_set.close()
	else :					#if server not reachable
		file_set = open("settings.txt", 'r')
		settings_file = file_set.read()
		settings = json.loads(settings_file)
	return settings


def play_in_sound():
   os.system("aplay /home/andrej/project_portals/in.wav")
def play_out_sound():
   os.system("aplay /home/andrej/project_portals/out.wav")
