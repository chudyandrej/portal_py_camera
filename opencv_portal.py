import numpy as np
import cv2
import thread
import time
import math
import random
from sets import Set
from tracked_object import TrackedObject
from collections import namedtuple
from bg_subtractor import frames, start_threads, load_settings
from comunication import send_transaction

min_area = 2200
max_dist_to_pars = 60
min_dis_to_create = 70
penalt = 20

frame_width = 320
frame_height = 240
pass_in = 0
pass_out = 0

def erode_dilate(fgmask):
    kernel = np.ones((5,5),np.uint8)
    erosion = cv2.erode(fgmask,kernel,iterations = 1)
    dilation = cv2.dilate(erosion,kernel,iterations = 2)
    return dilation

def find_contours(filtered_fgmask):
    _ , contours, _ = cv2.findContours(filtered_fgmask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) 
    valid_contours = filter(lambda cnt: cv2.contourArea(cnt) > min_area, contours)  #filter contours bigger as min_area
    valid_contour_objects = []
    #create conture_object 
    for contour in valid_contours:
        x, y, w, h = cv2.boundingRect(contour)
        Point_tuple = namedtuple('Point', 'x y')
        Contour_tuple = namedtuple('Contour', 'point size cnt obj_count')
        size = (w, h)
        center_point = Point_tuple(x+w/2, y+h/2)
        #whit information: center_point, size , contour, counter objects of interest
        valid_contour_objects.append(Contour_tuple(center_point, size, contour, [0]))

    return valid_contour_objects

def calc_distance(point1, point2):
    #calc absolut distance whit benefit on y 
    a = (point1[0] - point2[0]) 
    b = (point1[1] - point2[1]) / 1.5
    return  math.sqrt(a**2 + b**2)

def parse_contours(contours, tracked_objects,t):
    distances = []  #create list of distances betwen tracked_objects and contours
    potential_relicts = []  #create list of potential_relicts contours

    for obj in tracked_objects:
        for cnt in contours:
            distance = calc_distance(obj.get_prediction(t),cnt.point)
            if(distance < max_dist_to_pars):
                distances.append((obj, cnt, distance))
            if distance < min_dis_to_create:
                potential_relicts.append(cnt)

    distances = sorted(distances, key=lambda d : d[2])  #Sort from smallest
   
    seen = []

    for distance in distances:
        obj, cnt, _ = distance
        if obj not in seen:
            seen.append(obj)
            cnt.obj_count[0] += 1   #counter of objects of interest

    distances = map(lambda d :(d[0], d[1], d[2] + d[1].obj_count[0]*penalt), distances) #penalt calculation
    distances = sorted(distances, key=lambda d : d[2])  #sort one more

    used_objects = []
    used_cnts = []
    pairs = []

    for distance in distances:
        obj, cnt, _ = distance
        if obj not in used_objects: 
            used_objects.append(obj)    #push to used_objects
            if cnt in used_cnts:        #if more objects use the same contour
                pairs = filter(lambda p: p[1] != cnt, pairs)    #delete this conture
            else :
                pairs.append((obj, cnt))    #push to pairs

            used_cnts.append(cnt)   #push to used_cnts

    unused_objects = [obj for obj in tracked_objects if obj not in used_objects]    #select unused_objects
    unused_cnts_without_relicts = [cnt for cnt in contours 
            if cnt not in used_cnts and cnt not in potential_relicts]   #select only valid objects

    return pairs, unused_cnts_without_relicts, unused_objects


def create_objects(unused_cnts, tracked_objects, t):
    #create bjects from unused_cnts
    pause = False
    for cnt in unused_cnts:
        new_obj = TrackedObject(cnt.point.x, cnt.point.y, t)
        
        pause = True
        
        tracked_objects.append(new_obj)
        return pause

def update_pairs(pairs, t):
    #update position old objects
    for pair in pairs:
        obj, cnt = pair
        obj.update(cnt.point.x, cnt.point.y, t)

def update_missing(unused_objects, tracked_objects):
    #update information about missing object
    for unused_object in unused_objects:
        if unused_object.missing() == -1:
            tracked_objects.remove(unused_object)
  
def abs_disto_obj(tracked_object, t):
    #calculate abosult distace from start position to prediction position
    global pass_in 
    global pass_out
    distance = tracked_object.start_y - tracked_object.get_prediction(t).y
    if distance < 0:    
        if abs(distance) > frame_height / 2:        
            pass_in += 1
            print "in: " + str(pass_in)
            thread.start_new_thread(send_transaction,(1525458,'in'))
            return 0              
    else: 
        if abs(distance) > frame_height / 2:
            pass_out += 1
            print "out: " + str(pass_out)
            thread.start_new_thread(send_transaction,(1525458,'out'))
            return 0
    return 1


def counter_person_flow(tracked_objects, t):
    #create countering lines
    for tracked_object in tracked_objects:
        if (tracked_object.start_y < frame_height / 2 and 
                tracked_object.get_prediction(t).y > frame_height - frame_height / 4 ): #up line 
            if abs_disto_obj(tracked_object, t) == 0:   #object-counting 
                tracked_object.start_y = frame_height
                tracked_object.changed_starting_pos = True
            
        if (tracked_object.start_y > frame_height / 2 and
                tracked_object.get_prediction(t).y < frame_height / 4 ):    #down line
            if abs_disto_obj (tracked_object, t) == 0:  #object-counting
                tracked_object.start_y = 0
                tracked_object.changed_starting_pos = True
                
def start_tracking():
    cv2.namedWindow('frame', 0)             #init windows
    cv2.namedWindow('filtered_fgmask', 0) 
    
    global min_area
    global max_dist_to_pars
    global min_dis_to_create
    global penalt
    min_area, max_dist_to_pars, min_dis_to_create, penalt  = load_settings()

    start_threads()
    tracked_objects = []

    t = 1
    while(True):
        #print "q.size " + str(frames.qsize())
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
            frame = cv2.rectangle(frame, (x,y), (x+w,y+h), obj.color)
            frame = cv2.circle(frame, obj.get_prediction(t), 10, obj.color, -1)
            frame = cv2.ellipse(frame, obj.get_prediction(t), (60, 90), 0, 0, 360, obj.color)          

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

      


