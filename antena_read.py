import random
import thread
import time
import socket
import sys
import binascii



POLL_INTERVAL = 0.01
TIME_TO_KEEP_TAGS = 20
TAG_WINDOW_LENGTH = 2
SIGNAL_THRESHOLD = 0.3
class AntennaReader():




    def read_forever(self):

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the address given on the command line
        server_address = ('', 8888)
        sock.bind(server_address)
        print >>sys.stderr, 'starting up on %s port %s' % sock.getsockname()
        sock.listen(1)

        while True:
            print >>sys.stderr, 'waiting for a connection'
            connection, client_address = sock.accept()
            try:
                print >>sys.stderr, 'client connected:', client_address
                while True:
                    data = connection.recv(1000)
                    if not data:
                        break
                    data = data.replace("\x00", "")
                    data = data.replace("\r", "")
                    
                    tags = data.split('\n')
                    
                    for tag_string in tags:
                        tag = tag_string.split(',')
                        if len(tag) == 4:
                            print int(tag[1], 16) & 0xffffff

                            self.tag_list.append((int(tag[1], 16) & 0xffffff,float(tag[3]), time.time()))
                self.tag_list = filter(lambda tag: tag[2] > time.time() - TIME_TO_KEEP_TAGS , self.tag_list)

                    
            finally:
                print "connection closed"
                connection.close()

    def __init__(self):
        self.tag_list = []
        thread.start_new_thread(self.read_forever, ())

    
   
    
    def get_object_tag_id(self, center_time):
       
        min_time = center_time - TAG_WINDOW_LENGTH
        max_time = center_time + TAG_WINDOW_LENGTH
        valid_tags = filter(lambda tag: tag[2] > min_time and tag[2] < max_time, self.tag_list)

        if not valid_tags:
            return -1, True
        max_tuple = max(valid_tags, key=lambda tag: tag[1])
        max_signal = max_tuple[1]
        certainity = True
        for tag in valid_tags:
            if tag[0] != max_tuple[0] and tag[1] > max_signal - SIGNAL_THRESHOLD:
                certainity = False
        self.tag_list = filter(lambda tag: tag[0] != max_tuple[0], self.tag_list)


        scale = 16 ## equals to hexadecimal

        

        tag_ID = max_tuple[0]
        return tag_ID, certainity

		
