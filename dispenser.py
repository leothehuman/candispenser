import RPi.GPIO as GPIO
import board
import neopixel
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.blink import Blink
from time import time, sleep
from pygame import mixer
from os import listdir
from os.path import isfile, join
from random import choice
from notifiers import get_notifier
from datetime import datetime

SENS = 4
TRIG = 23
ECHO = 24
DIR = 20   # Direction GPIO Pin
STEP = 21  # Step GPIO Pin
ENA = 16   # Enable GPIO Pin
CW = 0     # Clockwise Rotation
CCW = 1    # Counterclockwise Rotation
FWD = CCW
BKW = 1 - FWD

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
max_steps_till_contact = 8000;
telegram = get_notifier('telegram')

FAR = 35
CLOSE = 30

pixels = neopixel.NeoPixel(board.D18, 30, auto_write = False)

def step(delay1, delay2):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay1)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay2)

def measure(prev):
    sleep(0.1)
    GPIO.output(TRIG, GPIO.HIGH)
    sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    MAX_DELAY = 1000
    echo_delay = 0
    while not GPIO.input(ECHO) and echo_delay < MAX_DELAY:
        echo_delay += 1
    if not echo_delay < MAX_DELAY:
        return 1000
    pulse_start = time()
    while GPIO.input(ECHO):
        pass
    distance = (time() - pulse_start) * 17150
    print("Distance:", int(distance), "cm   ", end = ('\n' if bool(distance > FAR) and bool(prev) or bool(distance < CLOSE) and not bool(prev) else '\r'))
    return distance

def steps(sdir, delay1, delay2, smin, smax, cond):
    GPIO.output(DIR, sdir)
    s = 0
    while s < smin or (cond() and s < smax):
        s += 1
        step(delay1, delay2)
        animation.animate()
    return s

with open('telegram_notifier_token', 'r') as file:
    token = file.read().strip()
with open('telegram_chat_id', 'r') as file:
    chat_id = file.read().strip()

path = '/home/pi/sounds'
sounds = [f for f in listdir(path) if isfile(join(path, f))]
sound = None
channel = None
sound_start_time = datetime.now()
mixer.init()

try:
    while True:
        animation = Blink(pixels, color = (255, 0, 0), speed = 0.5)
        untriggered = 0
        while untriggered < 3:
            distance = measure(untriggered < 3)
            if distance > FAR:
                untriggered += 1
            else:
                untriggered = 0
            animation.animate()
            sleep(0.1)
        print("Ready for a bucket!")

        animation = Solid(pixels, color = (0, 0, 0))
        animation.animate()
        animation = SparklePulse(pixels, speed = 0.05, color = (255, 70, 0), period = 0.1, min_intensity = 0.1, max_intensity = 0.7)

        triggered = 0
        while triggered < 3:
            distance = measure(triggered > 2)
            if distance < CLOSE and distance > 0:
                triggered += 1
            else:
                triggered = 0
            animation.animate()
            sleep(0.1)
        print("Triggered!")

        if channel and channel.get_busy():
            print("Still playing", sound)
        else:
            print("Done with", sound, "after", datetime.now() - sound_start_time)
            sound = choice(sounds)
            print("Playing", sound)
            sound_start_time = datetime.now()
            channel = mixer.Sound(join(path, sound)).play()

        animation = Solid(pixels, color = (0, 255, 0))
        print("Dispensing...")
        try:
            GPIO.output(ENA, GPIO.LOW)
            steps_till_clear = steps(BKW, delay, delay, 0, 100, lambda: not GPIO.input(SENS))
            steps_till_contact = steps(FWD, delay, delay, 0, max_steps_till_contact, lambda: GPIO.input(SENS))
            clear_steps = steps(FWD, delay, delay, 200, 500, lambda: not GPIO.input(SENS))
            backup_steps = steps(BKW, delay, delay, 10, 100, lambda: not GPIO.input(SENS))
        finally:
            GPIO.output(ENA, GPIO.HIGH)

        step_counts = str(steps_till_contact) + ' steps and ' + str(clear_steps) + ' clear steps and ' + str(backup_steps) +' backup steps'
        if steps_till_contact < max_steps_till_contact:
            message = 'Dispensed after ' + step_counts
            # telegram.notify(message = message, token = token, chat_id = chat_id)
            print(" ", message)
        else:
            message = 'FAILED after ' + step_counts
            telegram.notify(message = message, token = token, chat_id = chat_id)
            print(" ", message)
finally:
    pass
