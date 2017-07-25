#!/usr/bin/python3

import threading
import time

exitFlag = 0

class myThread (threading.Thread):
    def __init__(self, p_Name):
        threading.Thread.__init__(self)
        self.name= p_Name
        self.counter= 0
    def run(self):
        print ("Starting " + self.name)
        while not exitFlag:
          print ("%s: %s %s" % (self.name, time.ctime(time.time()), self.counter))
          self.counter += 1
          time.sleep(1)
        print ("Exiting " + self.name)

# Create new threads
thread1 = myThread("Thread-1")
thread2 = myThread("Thread-2")


# Start new Threads
thread1.start()
time.sleep(0.5)
thread2.start()

try :
  while True :
    time.sleep(0.1)
except KeyboardInterrupt :
  exitFlag= 1
  thread1.join()
  thread2.join()
  print ("Exiting Main Thread")


