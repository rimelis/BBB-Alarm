#!/usr/bin/python3

import subprocess
import threading
import time

exitFlag = 0

class ProcessInputThread (threading.Thread):
    def __init__(self, p_gpio_name, p_func_name):
        threading.Thread.__init__(self)
        self.__title= p_gpio_name
#        self.__irq= "cat /proc/interrupts | grep " + p_irq_name
#        self.__prev_irq_count= None
#        self.__curr_irq_count= None
#        self.__gpio_file= "/sys/class/gpio/" + p_gpio_name + "/value"
        self.__file= open("/sys/class/gpio/" + p_gpio_name + "/value", "r+")
        self.__prev_value= None
        self.__curr_value= None
        self.__debounce_counter= 0
        self.__func_name= p_func_name
    def run(self):
        print ("Starting " + self.__title)
        while not exitFlag:
            self.__file.seek(0, 0)
            self.__curr_value= int(self.__file.read(1))
            if self.__curr_value != self.__prev_value :
                self.__debounce_counter= 2
                while self.__debounce_counter > 0 :
                    self.__file.seek(0, 0)
                    self.__curr_value= int(self.__file.read(1))
                    if self.__prev_value == self.__curr_value :
                        self.__debounce_counter -= 1
                    else :
                        self.__prev_value= self.__curr_value
                        self.__debounce_counter= 2
                    time.sleep(0.1)

            # Reiksme pasikeite
            print ("%s: %s %s" % (self.__title, time.ctime(time.time()), self.__curr_value))
            globals()[self.__func_name](self.__curr_value)
            time.sleep(0.1)
        print ("Exiting " + self.__title)


def SwitchOutput(p_gpio_name, p_value) :
  if p_value == 0 :
    l_value= 1
  else :
    l_value= 0
  l_call= 'echo ' + str(l_value) + ' > /sys/class/gpio/' + p_gpio_name + '/value'
  cmd_out= subprocess.check_call(l_call, shell=True)

def TestSwitch(p_value) :
  dummy= 'foo'


threads = []

thread = ProcessInputThread("gpio69", "TestSwitch")
threads.append(thread)

# Start new Threads
for t in threads :
  t.start()

try :
  while True :
    time.sleep(0.1)
except KeyboardInterrupt :
  exitFlag= 1
  for t in threads :
    t.join()
  print ("Exiting Main Thread")


'''cmd_out= subprocess.check_output("cat /proc/interrupts | grep alarm_in_4", shell=True)
cmd_out_array= cmd_out.split()
irq_count= int(cmd_out_array[1])

print(irq_count)
'''
