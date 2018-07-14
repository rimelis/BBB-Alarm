import serial
import time
import logging
import logging.handlers
import configparser
from os import path
import traceback
import queue

from classes import Area, Zone, KeySwitch, SystemEvent, AreaEvent, KeySwitchEvent, MQTTClient

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

COMMON_PANEL_PASSWORD= config['COMMON']['panel_password']

COM_TTY_PORT= config['COM_TTY']['port']
COM_TTY_BAUD_RATE= int(config['COM_TTY']['baud_rate'])


# Configure logging to log to a file, making a new file at midnight and keeping the last 7 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger("prt_processor_logger")
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, mode='a', maxBytes=1*1024*1024,
                                 backupCount=10, encoding=None, delay=0)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(module)s - %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Console logger
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


# Exception logger into one log line
def log_app_error(e: BaseException, level=logging.ERROR) -> None:
    e_traceback = traceback.format_exception(e.__class__, e, e.__traceback__)
    traceback_lines = []
    for line in [line.rstrip('\n') for line in e_traceback]:
        traceback_lines.extend(line.splitlines())
    logger.log(level, traceback_lines.__str__())


# Custom serial redaline to carry CR instead of LN
def serial_read_line(ser):
    str = ""
    while True:
        ch = ser.read()
        if(ch == b'\r' or ch == b'' and len(str) == 0):
            break
        str += ch.decode('ascii')
    return str


#####################################################################################################

if __name__ == '__main__':
    logger.debug("vvvvv---------v---------vvvvv")
    logger.info("Initializing...")

    # Global MQTT and Serial output queue
    SerialOutQueue = queue.Queue()

    mqtt = MQTTClient(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, MQTT_BROKER_USER, MQTT_BROKER_PASSWORD, SerialOutQueue)

    RAList= []
    AAList= []
    ADList= []
    KSList= []

    ser = serial.Serial(
        port=COM_TTY_PORT,
        baudrate=COM_TTY_BAUD_RATE,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )

    if ser.isOpen():
        logger.info("SERIAL {0:s} is OPENED.".format(COM_TTY_PORT))
        try:
          while True:
            # reading serial
            instr = serial_read_line(ser)
            if len(instr) > 0 :
              logger.debug(">"+instr)
              if instr == "exit" :
                  break
              elif instr[0:1] == 'G' :
                  try:
                      se= SystemEvent(instr)
                      print(se)
                      del se
                  except Exception as e:
                      log_app_error(e)
              elif instr[0:2] == 'RA' :
                  try:
                      if len(instr) == 5 :
                        ra= next((x for x in RAList if x.call_str[0:5] == instr[0:5]), None)
                        if not ra:
                            ra= AreaEvent(instr)
                            RAList.append(ra)
                            logger.debug(ra)
                      else :
                          if len(instr) == 12 :
                            ra= next((x for x in RAList if x.call_str[0:5] == instr[0:5]), None)
                            if ra:
                                logger.debug("Request Area answer received.")
                                ra.answer(instr)
                                mqtt.publish(ra.area.mqtt_topic, ra.area.payload)
                                RAList.remove(ra)
                                del ra
                            else :
                                logger.debug("Request Area answer {0:s} has not found the initiator!".format(instr))
                          else :
                              logger.debug("Wrong Request Area answer")
                  except Exception as e:
                      log_app_error(e)
              elif instr[0:2] == 'AA':
                  try:
                      if (len(instr) >= 5) and (len(instr) <= 6) :
                          aa = next((x for x in AAList if x.call_str[0:5] == instr[0:5]), None)
                          if not aa:
                              aa = AreaEvent(instr)
                              AAList.append(aa)
                              logger.debug(aa)
                      else:
                          aa = next((x for x in AAList if x.call_str[0:5] == instr[0:5]), None)
                          if aa:
                              logger.debug("Area arm answer received.")
                              aa.answer(instr)
                              AAList.remove(aa)
                              del aa
                          else:
                              logger.debug("Area arm answer {0:s} has not found the initiator!".format(instr))
                  except Exception as e:
                      log_app_error(e)
              elif instr[0:2] == 'AD':
                  try:
                      if (len(instr) >= 5) and (len(instr) <= 6) :
                          ad = next((x for x in ADList if x.call_str[0:5] == instr[0:5]), None)
                          if not ad:
                              ad = AreaEvent(instr)
                              ADList.append(ad)
                              logger.debug(ad)
                      else:
                          ad = next((x for x in ADList if x.call_str[0:5] == instr[0:5]), None)
                          if ad:
                              logger.debug("Area disarm answer received.")
                              ad.answer(instr)
                              ADList.remove(ad)
                              del ad
                          else:
                              logger.debug("Area disarm answer {0:s} has not found the initiator!".format(instr))
                  except Exception as e:
                      log_app_error(e)
              elif instr[0:2] == 'UK':
                  try:
                      if len(instr) == 5 :
                          ks = next((x for x in KSList if x.call_str[0:5] == instr[0:5]), None)
                          if not ks:
                              ks = KeySwitchEvent(instr)
                              KSList.append(ks)
                              logger.debug(ks)
                      else:
                          ks = next((x for x in KSList if x.call_str[0:5] == instr[0:5]), None)
                          if ks:
                              logger.debug("Utility key event answer received.")
                              ks.answer(instr)
                              KSList.remove(ks)
                              del ks
                          else:
                              logger.debug("Utility key event answer {0:s} has not found the initiator!".format(instr))
                  except Exception as e:
                      log_app_error(e)
              else:
                  logger.debug("Unknown input.")

            # writing to serial
            if not SerialOutQueue.empty():
                strCommand = SerialOutQueue.get()
                if strCommand:
                    ser.write(strCommand.encode('ascii'))

            time.sleep(0.1)
        except KeyboardInterrupt :
            print("Stopped.")
        except Exception as e:
            log_app_error(e)

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

    del mqtt
    ser.close()

    logger.info("Stopped.")
    logger.debug("^^^^^---------^---------^^^^^")
