import serial
import time
import logging
import logging.handlers 

LOG_FILENAME = '/media/card/alarm/log/PRT_comm.log'

PrtCommLogger= logging.getLogger('PrtCommLogger')
PrtCommLogger.setLevel(logging.DEBUG)
PrtCommLogHandler= logging.handlers.TimedRotatingFileHandler(
              LOG_FILENAME,
              when= 'midnight',
              backupCount= 0
              )
PrtCommLogFormatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
PrtCommLogHandler.setFormatter(PrtCommLogFormatter)
PrtCommLogger.addHandler(PrtCommLogHandler)

ser = serial.Serial(
  port = "/dev/ttyO2",
  baudrate=57600,
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
