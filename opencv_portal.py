import numpy as np
import cv2
from sets import Set
from tracked_object import TrackedObject
from collections import namedtuple
from bg_subtractor import frames, main
from load_data import get_json_config

import time
import math
import random
learning_history = 1000
thresholding = 1300
min_area = 2200
shadow_thresh = 0.7
max_dist_to_pars = 60
min_dis_to_create = 70
frame_width = 320
frame_height = 240
pass_in = 0
pass_out = 0

def init_bg_substractor():
    
    bg_subtractor = cv2.createBackgroundSubtractorKNN()
    bg_subtractor.setShadowThreshold(shadow_thresh)
    bg_subtractor.setDetectShadows(True)
    bg_subtractor.setDist2Threshold(thresholding)
    bg_subtractor.setHistory(learning_history)
    bg_subtractor.setShadowValue(0)
    return bg_subtractor

def exit_program(cap):
    cap.release()
    cv2.destroyAllWindows()

def apply_subtractor(frame, bg_subtractor):
    return bg_subtractor.apply(frame)

def erode_dilate(fgmask):
    kernel = np.ones((5,5),np.uint8)
    erosion = cv2.erode(fgmask,kernel,iterations = 1)
    dilation = cv2.dilate(erosion,kernel,iterations = 2)
    return dilation

def find_contours(filtered_fgmask):
    _ , contours, _ = cv2.findContours(filtered_fgmask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    valid_contours = filter(lambda cnt: cv2.contourArea(cnt ) > min_area, contours)
    valid_contour_objects = []
    for cnt in valid_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        Point = namedtuple('Point', 'x y')
        Contour = namedtuple('Contour', 'point size cnt id obj_count')
        size = (w, h)
        pt = Point(x+w/2, y+h/2)
        id = int( random.random() * 100)
      
        
        valid_contour_objects.append(Contour(pt, size, cnt, id, [0]))

    return valid_contour_objects

def calc_distance(point1, point2):
    a = (point1[0] - point2[0]) 
    b = (point1[1] - point2[1]) / 1.5
    return  math.sqrt(a**2 + b**2)

def parse_contours(contours, tracked_objects,t):
    distances = []
    potential_relicts = []

    for obj in tracked_objects:
        for cnt in contours:
            distance = calc_distance(obj.get_prediction(t),cnt.point)
            if(distance < max_dist_to_pars):
                distances.append((obj, cnt, distance))
            if distance < min_dis_to_create:
                potential_relicts.append(cnt)

    distances = sorted(distances, key=lambda d : d[2])
   
    seen = []

    for distance in distances:
        obj, cnt, _ = distance
        if obj not in seen:
            seen.append(obj)
            cnt.obj_count[0] += 1

    distances = map(lambda d :(d[0], d[1], d[2] + d[1].obj_count[0]*20), distances)
    distances = sorted(distances, key=lambda d : d[2])
    used_objects = []
    used_cnts = []
    pairs = []

    for distance in distances:
        obj, cnt, _ = distance
        if obj not in used_objects:
            used_objects.append(obj)
            if cnt in used_cnts:
                pairs = filter(lambda p: p[1] != cnt, pairs)
            else :
                pairs.append((obj, cnt))

            used_cnts.append(cnt)

    unused_objects = [obj for obj in tracked_objects if obj not in used_objects]
    unused_cnts_without_relicts = [cnt for cnt in contours 
            if cnt not in used_cnts and cnt not in potential_relicts]

    return pairs, unused_cnts_without_relicts, unused_objects



def find_nearest(base_point, other_points):
    if not other_points:
        return -1
    i, point = min(enumerate(other_points), lambda p: calc_distance(base_point, p[1]))
    return i

def create_objects(unused_cnts, tracked_objects, t):
    pause = False
    for cnt in unused_cnts:
        new_obj = TrackedObject(cnt.point.x, cnt.point.y, t)
        
        pause = True
        
        tracked_objects.append(new_obj)
        return pause

def update_pairs(pairs, t):
    for pair in pairs:
        obj, cnt = pair
        obj.update(cnt.point.x, cnt.point.y, t)

def update_missing(unused_objects, tracked_objects):
    for unused_object in unused_objects:
        if unused_object.missing() == -1:
            
            tracked_objects.remove(unused_object)
  
def abs_disto_obj(tracked_object, t):
    global pass_in 
    global pass_out
    distance = tracked_object.start_y - tracked_object.get_prediction(t).y
    if distance < 0:
        if abs(distance) > frame_height / 2: 
            pass_in += 1
            print "in: " + str(pass_in)
            return 0              
    else: 
        if abs(distance) > frame_height / 2:
            pass_out += 1
            print "out: " + str(pass_out)
            return 0
    return 1


def counter_person_flow(tracked_objects, t):
    for tracked_object in tracked_objects:
        if (tracked_object.start_y < frame_height / 2 and 
                tracked_object.get_prediction(t).y > frame_height - frame_height / 4 ):
            if abs_disto_obj(tracked_object, t) == 0: 
                tracked_object.start_y = frame_height
                tracked_object.changed_starting_pos = True
            
        if (tracked_object.start_y > frame_height / 2 and
                tracked_object.get_prediction(t).y < frame_height / 4 ):
            if abs_disto_obj (tracked_object, t) == 0:
                tracked_object.start_y = 0
                tracked_object.changed_starting_pos = True


                
    




def start_tracking():
    cv2.namedWindow('frame', 0) 
    cv2.namedWindow('filtered_fgmask', 0) 
    settings = get_json_config('http://192.168.1.15:3000/api/portal_endpoint/settings/1', 'settings.txt')
    global learning_history
    learning_history = settings['learning_history']
    global thresholding
    thresholding = settings['thresholding']
    global min_area
    min_area = settings['min_area']
    global shadow_thresh
    shadow_thresh = settings['shadow_thresh']
    global max_dist_to_pars
    max_dist_to_pars = settings['max_dist_to_parse']
    global min_dis_to_create
    min_dis_to_create = settings['min_dist_to_create']


    main()
    cap = cv2.VideoCapture("/home/andrej/Music/colisions/video.mkv")
    bg_subtractor = init_bg_substractor()
    tracked_objects = []
    frame_delay = 50
    t = 10
    while(True):
        print "ahoj"
        print "q.size " + str(frames.qsize())
        frame , fgmask = frames.get(block=True)
        
        filtered_fgmask = erode_dilate(fgmask)
        contour_objects = find_contours(filtered_fgmask)
        t += 1

        pairs, unused_cnts, unused_objects = parse_contours(contour_objects, tracked_objects,t)
        pause = create_objects(unused_cnts, tracked_objects,t)
        update_pairs(pairs, t)
        update_missing(unused_objects,tracked_objects)
        counter_person_flow(tracked_objects, t)
        for obj in tracked_objects:
            cv2.putText(frame,str(obj.id), obj.get_prediction(t), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
            frame = cv2.circle(frame, obj.get_prediction(t), 5, obj.color, -1)
            
            frame = cv2.ellipse(frame, obj.get_prediction(t), (60, 90), 0, 0, 360, obj.color)
        for pair in pairs:
            obj, cnt = pair
            
            w = cnt.size[0]
            h = cnt.size[1]
            x = cnt.point.x - w/2
            y = cnt.point.y - h/2 
            cv2.putText(frame,str(cnt.id), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 100)
            frame = cv2.rectangle(frame, (x,y), (x+w,y+h), obj.color)
            frame = cv2.circle(frame, obj.get_prediction(t), 10, obj.color, -1)
            frame = cv2.ellipse(frame, obj.get_prediction(t), (60, 90), 0, 0, 360, obj.color)          
            
        for cnt in unused_cnts:
            w = cnt.size[0]
            h = cnt.size[1]
            x = cnt.point.x - w/2
            y = cnt.point.y - h/2 
            cv2.putText(frame,str(cnt.id), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 100)
            frame = cv2.rectangle(frame, (x,y), (x+w,y+h), (255,255,255))
        

        frame = cv2.putText(frame,str(pass_in), (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255))
        frame = cv2.putText(frame,str(pass_out), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, 100 )

       
        cv2.imshow('frame',frame)
        cv2.imshow('filtered_fgmask',filtered_fgmask)



        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
        	break
        if key & 0xFF == ord('f'):
            frame_delay = 1
        if key & 0xFF == ord('s'):
            frame_delay = 1000
        if key & 0xFF == ord('l'):
            time.sleep(20)
        if key & 0xFF == ord('p'):
            time.sleep(2)

      

    exit_program(cap)
