#!/usr/bin/env python3

import subprocess
import threading
import time
import sys
import logging
import logging.handlers
import signal
import configparser


# Defaults
LOG_FILENAME = '/media/card/alarm/log/alarm_gpio.log'
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"

#Opening config
config= configparser.ConfigParser()
config.read('/home/debian/daemon/alarm_gpio.ini')

LOG_FILENAME= config['LOGGING']['filename']
LOG_LEVEL= int(config['LOGGING']['level'])
GPO_VARTAI= config['OUTPUTS']['gpo_vartai']
GPO_GARAZAS= config['OUTPUTS']['gpo_garazas']

# Configure logging to log to a file, making a new file at midnight and keeping the last 7 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, mode='a', maxBytes=1*1024*1024,
                                 backupCount=10, encoding=None, delay=0)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class DaemonLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level
        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())
        def flush(self):
            pass

# Replace stdout with logging to file at INFO level
sys.stdout = DaemonLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = DaemonLogger(logger, logging.ERROR)

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)
  def exit_gracefully(self,signum, frame):
    self.kill_now = True

""" BODY """

exitFlag = 0

class ProcessGPIOThread (threading.Thread):
    def __init__(self, p_name, p_gpio_name, p_func_name):
        threading.Thread.__init__(self)
        self.__title= p_name
        logger.debug("THR(" + self.__title + "): Initializing.")
        logger.debug("THR(" + self.__title + "): GPIO=" + p_gpio_name)
        self.__file= open("/sys/class/gpio/" + p_gpio_name + "/value", "r+")
        self.__prev_value= None
        self.__curr_value= None
        self.__debounce_counter= 0
        self.__func_name= p_func_name
        logger.debug("THR(" + self.__title + "): Function= " + self.__func_name)
    def run(self):
        logger.debug("THR(" + self.__title + "): Starting.")
        while not exitFlag:
            self.__file.seek(0, 0)
            self.__curr_value= int(self.__file.read(1))
            if self.__curr_value != self.__prev_value :
                self.__prev_value= self.__curr_value
                self.__debounce_counter= 3
                while self.__debounce_counter > 0 :
                    self.__file.seek(0, 0)
                    self.__curr_value= int(self.__file.read(1))
                    if self.__prev_value == self.__curr_value :
                        self.__debounce_counter -= 1
                    else :
                        self.__prev_value= self.__curr_value
                        self.__debounce_counter= 3
                    time.sleep(0.05)
                # Reiksme pasikeite
                logger.info(self.__title + ": value > " + str(self.__curr_value))
                logger.debug("THR(" + self.__title + "): calling " + \
                             self.__func_name + "(" + str(self.__curr_value) + ")")
                globals()[self.__func_name](self, self.__curr_value)
            time.sleep(0.1)
        logger.debug("THR(" + self.__title + "): exiting.")
        self.__file.close()

    def SwitchOutput(self, p_gpio_name, p_value) :
#      l_call= 'echo ' + str(p_value) + ' > /sys/class/gpio/' + p_gpio_name + '/value'
      with open("/sys/class/gpio/" + p_gpio_name + "/value", "w") as l_file:
          l_file.write(str(p_value))
          l_file.close()
      logger.debug("THR(" + self.__title + "): SwitchOutput(" +p_gpio_name+ ") > " + str(p_value))
#      cmd_out= subprocess.check_call(l_call, shell=True)


def ToggleGarazas(p_caller_obj, p_value) :
  if p_value == 0 :
    l_value= 1
  else :
    l_value= 0
  p_caller_obj.SwitchOutput(GPO_GARAZAS, l_value)

def ToggleVartai(p_caller_obj, p_value) :
  if p_value == 0 :
    l_value= 1
  else :
    l_value= 0
  p_caller_obj.SwitchOutput(GPO_VARTAI, l_value)


if __name__ == '__main__':

  logger.debug("vvvvv-----------------vvvvv")
  logger.info("Initializing...")

  killer = GracefulKiller()
  threads = []

  thread = ProcessGPIOThread("Garazas", "gpio72", "ToggleGarazas")
  threads.append(thread)
  thread = ProcessGPIOThread("VartaiPultelis", "gpio117", "ToggleVartai")
  threads.append(thread)
  thread = ProcessGPIOThread("VartaiTelefonas", "gpio49", "ToggleVartai")
  threads.append(thread)

  # Start new Threads
  for t in threads :
    t.start()

  logger.info("Started.")
  logger.debug(">>>>>-----------------------")

  while True:
    time.sleep(1)
    if killer.kill_now :
      exitFlag= 1
      for t in threads :
        t.join()
      break

  logger.info("Stopped.")
  logger.debug("^^^^^-------------------^^^^^")
