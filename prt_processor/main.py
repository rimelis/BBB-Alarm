import logging
import logging.handlers
import configparser
from os import path
import traceback
import paho.mqtt.client as MQTTClient

from classes import Area, Zone, KeySwitch, SystemEvent, AreaEvent, KeySwitchEvent

# Defaults
LOG_FILENAME = '/media/card/prt_processor/log/prt_processor.log'
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"

# Opening config
config= configparser.ConfigParser()
config_file_path = path.join(path.dirname(path.abspath(__file__)), 'params.ini')
if not path.exists(config_file_path):
    config_file_path= '/home/debian/prt_processor/params.ini'
config.read(config_file_path)

LOG_FILENAME= config['LOGGING']['filename']
LOG_LEVEL= int(config['LOGGING']['level'])

MQTT_BROKER_ADDRESS= config['MQTT_BROKER']['address']
MQTT_BROKER_PORT= int(config['MQTT_BROKER']['port'])
MQTT_BROKER_USER= config['MQTT_BROKER']['user']
MQTT_BROKER_PASSWORD= config['MQTT_BROKER']['password']

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

# Console logger
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)

#####################################################################################################

if __name__ == '__main__':
    logger.debug("vvvvv---------v---------vvvvv")
    logger.info("Initializing...")


    RAList= []
    AAList= []
    ADList= []
    KSList= []

    try:
      while True:
        instr= input(">")
        if len(instr) > 0 :
          if instr == "exit" :
              break
          elif instr[0:1] == 'G' :
              try:
                  se= SystemEvent(instr)
                  print(se)
                  del se
              except:
                  formatted_lines = traceback.format_exc().splitlines()
#                  print (formatted_lines[-1])
                  print (formatted_lines)
          elif instr[0:2] == 'RA' :
              try:
                  if len(instr) == 5 :
                    ra= next((x for x in RAList if x.call_str[0:5] == instr[0:5]), None)
                    if not ra:
                        ra= AreaEvent(instr)
                        RAList.append(ra)
                        print (ra)
                  else :
                      if len(instr) == 12 :
                        ra= next((x for x in RAList if x.call_str[0:5] == instr[0:5]), None)
                        if ra:
                            ra.answer(instr)
                            RAList.remove(ra)
                            del ra
                            print ("Request Area answer received.")
                        else :
                            print ("Request Area answer {0:s} has not found the initiator!".format(instr))
                      else :
                          print("Wrong Request Area answer")
              except:
                  formatted_lines = traceback.format_exc().splitlines()
#                  print (formatted_lines[-1])
                  print (formatted_lines)
          elif instr[0:2] == 'AA':
              try:
                  if (len(instr) >= 5) and (len(instr) <= 6) :
                      aa = next((x for x in AAList if x.call_str[0:5] == instr[0:5]), None)
                      if not aa:
                          aa = AreaEvent(instr)
                          AAList.append(aa)
                          print(aa)
                  else:
                      aa = next((x for x in AAList if x.call_str[0:5] == instr[0:5]), None)
                      if aa:
                          aa.answer(instr)
                          AAList.remove(aa)
                          del aa
                          print("Area arm answer received.")
                      else:
                          print("Area arm answer {0:s} has not found the initiator!".format(instr))
              except:
                  formatted_lines = traceback.format_exc().splitlines()
                  #                  print (formatted_lines[-1])
                  print(formatted_lines)
          elif instr[0:2] == 'AD':
              try:
                  if (len(instr) >= 5) and (len(instr) <= 6) :
                      ad = next((x for x in ADList if x.call_str[0:5] == instr[0:5]), None)
                      if not ad:
                          ad = AreaEvent(instr)
                          ADList.append(ad)
                          print(ad)
                  else:
                      ad = next((x for x in ADList if x.call_str[0:5] == instr[0:5]), None)
                      if ad:
                          ad.answer(instr)
                          ADList.remove(ad)
                          del ad
                          print("Area disarm answer received.")
                      else:
                          print("Area disarm answer {0:s} has not found the initiator!".format(instr))
              except:
                  formatted_lines = traceback.format_exc().splitlines()
                  #                  print (formatted_lines[-1])
                  print(formatted_lines)
          elif instr[0:2] == 'UK':
              try:
                  if len(instr) == 5 :
                      ks = next((x for x in KSList if x.call_str[0:5] == instr[0:5]), None)
                      if not ks:
                          ks = KeySwitchEvent(instr)
                          KSList.append(ks)
                          print(ks)
                  else:
                      ks = next((x for x in KSList if x.call_str[0:5] == instr[0:5]), None)
                      if ks:
                          ks.answer(instr)
                          KSList.remove(ks)
                          del ks
                          print("Utility key event answer received.")
                      else:
                          print("Utility key event answer {0:s} has not found the initiator!".format(instr))
              except:
                  formatted_lines = traceback.format_exc().splitlines()
                  #                  print (formatted_lines[-1])
                  print(formatted_lines)
          else:
              print ("Unknown input.")
    except KeyboardInterrupt :
      print("Stopped.")


    while len(RAList) > 0 :
        ra= RAList.pop()
        del ra
    while len(AAList) > 0 :
        aa= AAList.pop()
        del aa
    while len(ADList) > 0 :
        ad= ADList.pop()
        del ad
    while len(KSList) > 0 :
        ks= KSList.pop()
        del ks


    """
    test= SystemEvent("G001N005A003")
    print(test)
    """
