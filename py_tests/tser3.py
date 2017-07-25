import serial
from time import sleep 

ser = serial.Serial(
  port = "/dev/ttyO2",
  baudrate=57600,
  parity=serial.PARITY_NONE,
  stopbits=serial.STOPBITS_ONE,
  bytesize=serial.EIGHTBITS,
  timeout=3
)

if ser.isOpen():
  print("Serial is open. Start reading")
  try:
    while True:
      str= ser.readline()
      print(str)
      sleep(0.1)
  except KeyboardInterrupt:
    print("Stopped.")

ser.close()
