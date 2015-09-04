import cv2
from comunication import websockets
import thread
from Queue import Queue
from threading import Lock
from comunication import get_json_config

num_workers = 3 		#Number of worker threads								
cap_locks = [Lock() for i in range(0, num_workers)]		#init mutexes for capture
push_locks = [Lock() for i in range(0, num_workers)]	#init mutexes for push to queue

learning_history = 1000
thresholding = 3000
shadow_thresh = 0.7

frames = Queue(10)		#init queue of frams and bg masks

def init_capture():
	#inicializating capture
	cap = cv2.VideoCapture("/home/andrej/Music/video1/pi_video1.mkv")								
	cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) 
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
	#cap.set(cv2.CAP_PROP_SATURATION, 100)		#set SATURATION 0 - 100
	return cap

def load_settings():
	#load settings from server
	settings = get_json_config()
	
 	global learning_history
   	learning_history = settings['learning_history']
   	global thresholding
   	thresholding = settings['thresholding']
  	global shadow_thresh
   	shadow_thresh = settings['shadow_thresh']

   	min_area = settings['min_area']
   	max_dist_to_pars = settings['max_dist_to_pars']
   	min_dis_to_create = settings['min_dis_to_create']
   	penalt = settings['penalt']
   	return min_area, max_dist_to_pars, min_dis_to_create, penalt

def init_bg_subtractor():
	#inicializating bg_subtractor
   	bg_subtractor = cv2.createBackgroundSubtractorKNN()
   	bg_subtractor.setShadowThreshold(shadow_thresh)
   	bg_subtractor.setDetectShadows(True)
   	bg_subtractor.setDist2Threshold(thresholding)
   	bg_subtractor.setHistory(learning_history)
   	bg_subtractor.setShadowValue(0)
   	return bg_subtractor


def worker(index, bg_subtractor, cap):
	#workers to make bg substractr 
	while True:
	 	cap_locks[index].acquire(True)					#mutex to read frame
	 	_ , frame = cap.read()	 						#read frame												
	 	cap_locks[(index + 1) % num_workers].release()	#post mutex to read for next worker
	 	result = bg_subtractor.apply(frame)				#calculate bg substrat
	 	push_locks[index].acquire(True)					#mutex to push readed freme and fg mask
	 	frames.put((frame, result), block=True)			#result push to queue
	 	push_locks[(index + 1) % num_workers].release()	#post mutex to push for next worker


def start_threads():
	#function to start all thread of program
	cap = init_capture()					
	bg_subtractor = init_bg_subtractor()

	thread.start_new_thread(websockets,())	#start websocket thread
	#start all workers
	for i in range(0, num_workers):						
		cap_locks[i].acquire(True)
		push_locks[i].acquire(True)
		thread.start_new_thread(worker, (i, bg_subtractor, cap))

	cap_locks[0].release()
	push_locks[0].release()
