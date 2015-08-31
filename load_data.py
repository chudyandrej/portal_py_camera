import requests
import json

def get_request(url):
	try: 
		r = requests.get(url)
	except:
		return None ,None
	json_request = json.loads(r.text)
	return json_request , r.text

def get_json_config(url, file_name):
	settings, text = get_request(url)
	if settings != None:
		print 'somtu'
		file_set = open(file_name, 'w')
		file_set.write(text)
		file_set.close()
	else :
		file_set = open(file_name, 'r')
		settings_file = file_set.read()
		settings = json.loads(settings_file)
	return settings



