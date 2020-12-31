from time import sleep
import RPi.GPIO as GPIO

DIR = 20   # Direction GPIO Pin
STEP = 21  # Step GPIO Pin
ENA = 16   # Enable GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN) #, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

delay = .0208 / 2 / 16

GPIO.output(DIR, CCW)
GPIO.output(ENA, GPIO.LOW)

#for x in range(step_count):
while GPIO.input(4):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay)
while not GPIO.input(4):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay * 3)

GPIO.cleanup()
