import RPi.GPIO as GPIO
from time import time, sleep
from pygame import mixer
from os import listdir
from os.path import isfile, join
from random import choice
from notifiers import get_notifier

path = '/home/pi/sounds'
sounds = [f for f in listdir(path) if isfile(join(path, f))]
mixer.init()

SENS = 4
TRIG = 23
ECHO = 24
DIR = 20   # Direction GPIO Pin
STEP = 21  # Step GPIO Pin
ENA = 16   # Enable GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation

GPIO.setmode(GPIO.BCM)

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)
GPIO.setup(SENS, GPIO.IN)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

GPIO.output(DIR, CCW)
GPIO.output(TRIG, GPIO.LOW)
GPIO.output(ENA, GPIO.HIGH)

delay = .0208 / 2 / 16
max_steps = 8000;
telegram = get_notifier('telegram')

def step(delay1, delay2):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay1)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay2)

def measure():
    sleep(0.1)
    GPIO.output(TRIG, GPIO.HIGH)
    sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    MAX_DELAY = 1000
    echo_delay = 0
    while not GPIO.input(ECHO) and echo_delay < MAX_DELAY:
        echo_delay += 1
    pulse_start = time()
    while GPIO.input(ECHO):
        pass
    distance = (time() - pulse_start) * 17150
    print("Distance:", int(distance), "cm   ", end = ('\n' if distance < CLOSE else '\r'))
    return distance

CLOSE = 30
triggered = 0

try:
    while True:
        distance = measure()
        if distance < CLOSE:
            triggered += 1
        else:
            triggered = 0
        if triggered > 2:
            channel = mixer.Sound(join(path, choice(sounds))).play()
            triggered = 0
            print("Dispensing...")
            GPIO.output(ENA, GPIO.LOW)
            steps = 0
            while GPIO.input(SENS) and steps < max_steps:
                steps += 1
                step(delay, delay)
            while not GPIO.input(SENS):
                step(delay, delay * 3)
            sleep(1)
            GPIO.output(ENA, GPIO.HIGH)
            if steps < max_steps:
                telegram.notify(message = 'Dispensed after ' + str(steps) + ' steps', token = '1487867467:AAE0q6bg5TrW9j4XV-UDgZpTNREsfCfFNVs', chat_id = 268663377)
                print("  Dispensed after", steps, "steps")
                while measure() < CLOSE:
                    sleep(1)
            else:
                telegram.notify(message = 'FAILED TO DISPENSE', token = '1487867467:AAE0q6bg5TrW9j4XV-UDgZpTNREsfCfFNVs', chat_id = 268663377)
                print("  FAILED TO DISPENSE!!!")
            while channel.get_busy():
                sleep(0.1)
finally:
    GPIO.cleanup()
