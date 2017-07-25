import Adafruit_BBIO.GPIO as GPIO

# in4
in4= "P8_45"
GPIO.setup(in4, GPIO.IN, pull_up_down = GPIO.PUD_UP)

if GPIO.input(in4):
  print("HIGH")
else:
  print("LOW")

#GPIO.wait_for_edge(in4, GPIO.FALLING)
#print("Done.")
