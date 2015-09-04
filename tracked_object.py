
from __future__ import division
from collections import deque
import random
from collections import namedtuple
MAX_HISTORY = 15
MIN_DISTANCE_OF_PASS = 250
frame_width = 320;
frame_height = 240;
class TrackedObject():

    def __init__(self, x, y, time):
        self.history = deque()
        self.frames_since_start = 0
        self.update (x, y, time)
        self.frames_missing = 0
        self.start_x = x
        self.start_y = y
        self.changed_starting_pos = False
        self.id = int(255*random.random())

        self.color = (255*random.random(), 255*random.random(),
                255*random.random())




    def update (self, x, y, time):

        position = (x, y, time)
        if len(self.history) > MAX_HISTORY:
            self.history.popleft()
        self.history.append(position)
        self.frames_missing = 0
        self.frames_since_start += 1

    def get_position(self):
        Point = namedtuple('Point', 'x y')
        if (len(self.history) == 0) :
            return Point(0,0)
        return Point(self.history[-1][0], self.history[-1][1])

    def missing(self):
        self.frames_missing += 1

        if self.frames_missing > 10 or self.frames_since_start < 2:
            return -1
        else:
            return 0

   
    def get_prediction(self, current_t):
        Point = namedtuple('Point', 'x y')
        if (len(self.history) == 0) :
            return Point(0,0)
        if (len(self.history) == 1) :
            return Point(self.history[0][0],self.history[0][1])
        start_x = self.history[0][0]
        start_y = self.history[0][1]
        start_t = self.history[0][2]
        last_x = self.history[-1][0]
        last_y = self.history[-1][1]
        last_t = self.history[-1][2]

        time_since_start = last_t - start_t

        v_x = (last_x - start_x) / time_since_start
        v_y = ((last_y - start_y) / time_since_start ) * 1.5

        delta_t = current_t - last_t

        current_x = last_x + v_x * delta_t

        current_y = last_y + v_y * delta_t
     
        if current_x <= 0:
            current_x = 0
        if current_x >= frame_width:
            current_x = frame_width
        if current_y <= 0:
            current_y = 0
        if current_y >= frame_height:
            current_y = frame_height


        return Point(int(current_x), int(current_y))
