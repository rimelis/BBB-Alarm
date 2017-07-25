import serial
import time
import logging
import logging.handlers
import configparser 

"""
class IncommingMessage:
   def __init__(self):
       self.type= 'None'
       self.area= 0
       self.zone= 0
       self.uk= 0
"""           

config = configparser.ConfigParser()
config.read('prt_comm.ini')

#LOG_FILENAME = '/media/card/alarm/log/prt_comm.log'

PrtCommLogger= logging.getLogger('PrtCommLogger')
PrtCommLogger.setLevel(int(config['LOGGING']['level']))
PrtCommLogHandler= logging.handlers.TimedRotatingFileHandler(
              config['LOGGING']['filename'],
              when= 'midnight',
              backupCount= 0
              )
PrtCommLogFormatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
PrtCommLogHandler.setFormatter(PrtCommLogFormatter)
PrtCommLogger.addHandler(PrtCommLogHandler)

ser = serial.Serial(
  port = config['COM_PARAM']['port'],
  baudrate=int(config['COM_PARAM']['baud_rate']),
  parity=serial.PARITY_NONE,
  stopbits=serial.STOPBITS_ONE,
  bytesize=serial.EIGHTBITS,
  timeout=0
)

if ser.isOpen():
  print("Serial is open. Start reading")
  PrtCommLogger.info("Serial is open. Start reading")
  try:
    while True:
      str= ser.readline()
      if len(str) > 0:
        print(str)
        PrtCommLogger.debug(str)

      time.sleep(0.1)
  except KeyboardInterrupt:
    print("Stopped.")
    PrtCommLogger.info("Stopped.")  

ser.close()

