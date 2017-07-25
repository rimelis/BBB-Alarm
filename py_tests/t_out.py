import Adafruit_BBIO.GPIO as GPIO

out4= "P8_10"
GPIO.setup(out4, GPIO.OUT)
GPIO.output(out4, GPIO.LOW)
