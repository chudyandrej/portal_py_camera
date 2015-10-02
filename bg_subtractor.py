import cv2
from comunication import websockets
import thread
from Queue import Queue
from threading import Lock
from comunication import get_json_settings, get_list_tag
import time

###############SETTINGS##############################
NUM_WORKERS = 3         #Number of worker threads
LEARN_HISTORY = 1000
THRESHOLD = 3000
SHADOW_THRESHOLD = 0.7
#####################################################

frames = Queue(10)      #init queue of frams and bg masks
cap_locks = [Lock() for i in range(0, NUM_WORKERS)]     #init mutexes for capture
push_locks = [Lock() for i in range(0, NUM_WORKERS)]    #init mutexes for push to queue

def init_capture():
    #inicializating capture
    cap = cv2.VideoCapture(0)                               
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) 
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_SATURATION, 100)       #set SATURATION 0 - 100
    return cap

def load_settings():
    #load settings from server
    settings = get_json_settings()
    
    global LEARN_HISTORY
    LEARN_HISTORY = settings['learning_history']
    global THRESHOLD
    THRESHOLD = settings['thresholding']
    global SHADOW_THRESHOLD
    SHADOW_THRESHOLD = settings['shadow_thresh']

    min_area = settings['min_area']
    max_dist_to_pars = settings['max_dist_to_pars']
    min_dis_to_create = settings['min_dis_to_create']
    penalt = settings['penalt']
    return min_area, max_dist_to_pars, min_dis_to_create, penalt

def init_bg_subtractor():
    #inicializating bg_subtractor
    bg_subtractor = cv2.createBackgroundSubtractorKNN()
    bg_subtractor.setShadowThreshold(SHADOW_THRESHOLD)
    bg_subtractor.setDetectShadows(True)
    bg_subtractor.setDist2Threshold(THRESHOLD)
    bg_subtractor.setHistory(LEARN_HISTORY)
    bg_subtractor.setShadowValue(0)
    return bg_subtractor


def worker(index, bg_subtractor, cap):
    #workers to make bg substractr 
    while True:
        cap_locks[index].acquire(True)                  #mutex to read frame
        _ , frame = cap.read()                          #read frame                                             
        cap_locks[(index + 1) % NUM_WORKERS].release()  #post mutex to read for next worker
        result = bg_subtractor.apply(frame)             #calculate bg substrat
        push_locks[index].acquire(True)                 #mutex to push readed freme and fg mask
        frames.put((frame, result, time.time()), block=True)         #result push to queue
        push_locks[(index + 1) % NUM_WORKERS].release() #post mutex to push for next worker


def start_threads():
    #function to start all thread of program
    cap = init_capture()                    
    bg_subtractor = init_bg_subtractor()
    get_list_tag()

    thread.start_new_thread(websockets,()) #start websocket thread
    #start all workers
    for i in range(0, NUM_WORKERS):                     
        cap_locks[i].acquire(True)
        push_locks[i].acquire(True)
        thread.start_new_thread(worker, (i, bg_subtractor, cap))

    cap_locks[0].release()
    push_locks[0].release()
