import random
import thread
import time
import pudb
POLL_INTERVAL = 0.01
TIME_TO_KEEP_TAGS = 20
TAG_WINDOW_LENGTH = 1
SIGNAL_THRESHOLD = 0.3
class AntennaReader():


    def get_random_tags(self, n):
        new_tags = [] 
        num_random_tags = len(self.random_tags)
        for i in range(0,n):
            random_index = int(num_random_tags * random.random())
            new_tags.append((self.random_tags[random_index], random.random(), time.time()))

        return new_tags

    def poll_antenna(self):
        new_tags = self.get_random_tags(5)
        return new_tags

    def read_forever(self):
        while True:
            new_tags = self.poll_antenna()
            current_time = time.time()
            self.tag_list = filter(lambda tag: tag[2] > current_time - TIME_TO_KEEP_TAGS, self.tag_list)
            self.tag_list.extend(new_tags)
            time.sleep(0.01)

    def __init__(self):
        self.tag_list = []
        thread.start_new_thread(self.read_forever, ())
        # List of tags used for random testing
        self.random_tags = [666, 12345]
    
   
    
    def get_object_tag_id(self, center_time):
       
        min_time = center_time - TAG_WINDOW_LENGTH
        max_time = center_time + TAG_WINDOW_LENGTH
        valid_tags = filter(lambda tag: tag[2] > min_time and tag[2] < max_time, self.tag_list)
        # Find the tag with highest signal
        if not valid_tags:
            return -1, True
        max_tuple = max(valid_tags, key=lambda tag: tag[1])
        max_signal = max_tuple[1]
        certainity = True
        for tag in valid_tags:
            if tag[0] != max_tuple[0] and tag[1] > max_signal - SIGNAL_THRESHOLD:
                certainity = False
        self.tag_list = filter(lambda tag: tag[0] != max_tuple[0], self.tag_list)
        return max_tuple[0], certainity

		
