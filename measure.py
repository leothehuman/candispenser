import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO = 24

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

GPIO.output(TRIG, False)
time.sleep(2)

try:
    while True:
        GPIO.output(TRIG, True)

        time.sleep(0.00001)

        GPIO.output(TRIG, False)

        while GPIO.input(ECHO)==0:
            pass

        pulse_start = time.time()

        while GPIO.input(ECHO)==1:
            pass
        
        distance = (time.time() - pulse_start) * 17150

        print("Distance: ",round(distance,2)," cm")
        time.sleep(1)
finally:
    GPIO.cleanup()
