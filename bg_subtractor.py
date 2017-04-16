import cv2
import _thread
from queue import Queue
from threading import Lock

import time

###############SETTINGS##############################
NUM_WORKERS = 5         #Number of worker threads
LEARN_HISTORY = 600
THRESHOLD = 2000
SHADOW_THRESHOLD = 0.1
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
   
    #start all workers
    for i in range(0, NUM_WORKERS):                     
        cap_locks[i].acquire(True)
        push_locks[i].acquire(True)
        _thread.start_new_thread(worker, (i, bg_subtractor, cap))

    cap_locks[0].release()
    push_locks[0].release()
