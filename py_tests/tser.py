
import serial
  
ser = serial.Serial(port = "/dev/ttyO2", baudrate=57600)
ser.close()
ser.open()
if ser.isOpen():
  print("Serial is open!")
  str= "Hello World!\r\n"
  str_bytes= str.encode('ascii')
  ser.write(str_bytes)
ser.close()
