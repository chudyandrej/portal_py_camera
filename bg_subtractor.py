import cv2
import thread
from Queue import Queue
from threading import Lock
num_workers = 10
cap_locks = [Lock() for i in range(0, num_workers)]
push_locks = [Lock() for i in range(0, num_workers)]
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_SATURATION, 100)
learning_history = 1000
thresholding = 1300
shadow_thresh = 0.7
frames = Queue(10)
def init_bg_subtractor():
    bg_subtractor = cv2.createBackgroundSubtractorKNN()
    bg_subtractor.setShadowThreshold(shadow_thresh)
    bg_subtractor.setDetectShadows(True)
    bg_subtractor.setDist2Threshold(thresholding)
    bg_subtractor.setHistory(learning_history)
    bg_subtractor.setShadowValue(0)
    return bg_subtractor


def worker(index, bg_subtractor):
	while True:
		print "index:" + str(index)
	 	cap_locks[index].acquire(True)
	 	_ , frame = cap.read()	 																		
	 	cap_locks[(index + 1) % num_workers].release()
	 	result = bg_subtractor.apply(frame)
	 	push_locks[index].acquire(True)
	 	frames.put((frame, result), block=True)
	 	
	 	push_locks[(index + 1) % num_workers].release()


def main():
	bg_subtractor = init_bg_subtractor()
	
	for i in range(0, num_workers):
		cap_locks[i].acquire(True)
		push_locks[i].acquire(True)
		thread.start_new_thread(worker, (i, bg_subtractor))

	cap_locks[0].release()
	push_locks[0].release()