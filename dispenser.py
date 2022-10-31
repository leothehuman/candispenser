import board
import json
import neopixel
import RPi.GPIO as GPIO
import serial
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.helper import PixelSubset
from datetime import datetime
from notifiers import get_notifier
from os import listdir
from os.path import isfile, join
from pygame import mixer
from random import choice
from time import time, sleep

SENS = 4
TRIG = 23
ECHO = 24
DIR = 20   # Direction GPIO Pin
STEP = 21  # Step GPIO Pin
ENA = 16   # Enable GPIO Pin
FWD = 1    # Rotation direction

GPIO.setmode(GPIO.BCM)

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)
GPIO.setup(SENS, GPIO.IN)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

GPIO.output(DIR, FWD)
GPIO.output(TRIG, GPIO.LOW)
GPIO.output(ENA, GPIO.HIGH)

delay = .0208 / 2 / 16
max_steps_till_contact = 8000;
telegram = get_notifier('telegram')

FAR = 45
CLOSE = 40
MAX_DELAY = 10000

ser = serial.Serial("/dev/ttyS0", 115200)
if ser.is_open == False:
    ser.open()
pixels = neopixel.NeoPixel(board.D18, 32, auto_write = False)
# RGB
drop = PixelSubset(pixels, 0, 1)
# GBR
windows = PixelSubset(pixels, 1, 32)

def step(delay1, delay2):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay1)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay2)

def measureSonar():
    GPIO.output(TRIG, GPIO.HIGH)
    sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    echo_delay = 0
    while not GPIO.input(ECHO) and echo_delay < MAX_DELAY:
        echo_delay += 1
    if not echo_delay < MAX_DELAY:
        return MAX_DELAY
    pulse_start = time()
    while GPIO.input(ECHO):
        pass
    return (time() - pulse_start) * 17150

def measureLidar():
    global ser
    ser.reset_input_buffer()
    while True:
        count = ser.in_waiting
        if count > 8:
            recv = ser.read(9)
            ser.reset_input_buffer()
            s = sum(recv[0:7], 9) % 256
            if recv[0] == 89 and recv[1] == 89 and s == recv[8] : # 0x59 is 'Y'
                distance = recv[2] + recv[3] * 256
                strength = recv[4] + recv[5] * 256
                temperature = recv[6] + recv[7] * 256
                return (distance, strength, temperature/8 - 256)

def measure(prev):
    sonarDistance = measureSonar()
    lidarDistance = measureLidar()
    distance = lidarDistance[0] - 9 if sonarDistance > 100 else sonarDistance
    print("  Distance:", int(distance), "cm   (lidar: ", int(lidarDistance[0]), ", sonar: ", int(sonarDistance), ")   ", end = ('\n' if bool(distance > FAR) and bool(prev) or bool(distance < CLOSE) and not bool(prev) else '\r'))
    return distance

def steps(sdir, delay1, delay2, smin, smax, cond):
    GPIO.output(DIR, sdir)
    s = 0
    while s < smin or (cond() and s < smax):
        s += 1
        step(delay1, delay2)
        animation.animate()
    return s

with open('secrets.json', 'r') as file:
    secrets = json.load(file)

path = '/home/pi/sounds'
sounds = [f for f in listdir(path) if isfile(join(path, f))]
sound = None
channel = None
animation = None
sound_start_time = datetime.now()
mixer.init()

def wait_to_untrigger():
    print("Waiting for the removal of the bucket!")
    untriggered = 0
    while untriggered < 3:
        animation.animate()
        distance = measure(untriggered < 3)
        if distance > FAR:
            untriggered += 1
        else:
            if untriggered:
                print("Waiting for the removal of the bucket!")
            untriggered = 0
        sleep(0.1)

def wait_to_trigger():
    print("Ready for a bucket!")
    triggered = 0
    while triggered < 3:
        animation.animate()
        distance = measure(triggered > 2)
        if distance < CLOSE and distance > 0:
            triggered += 1
        else:
            if triggered:
                print("Ready for a bucket!")
            triggered = 0
        sleep(0.1)

def play_a_sound():
    global channel
    global sound
    global sound_start_time
    if channel and channel.get_busy():
        print("Still playing", sound)
    else:
        print("Done with", sound, "after", datetime.now() - sound_start_time)
        sound = choice(sounds)
        print("Playing", sound)
        sound_start_time = datetime.now()
        channel = mixer.Sound(join(path, sound)).play()

def dispense():
    print("Dispensing...")
    try:
        GPIO.output(ENA, GPIO.LOW)
        steps_till_clear = steps(1 - FWD, delay, delay, 0, 100, lambda: not GPIO.input(SENS))
        steps_till_contact = steps(FWD, delay, delay, 0, max_steps_till_contact, lambda: GPIO.input(SENS))
        clear_steps = steps(FWD, delay, delay, 200, 500, lambda: not GPIO.input(SENS))
        backup_steps = steps(1 - FWD, delay, delay, 10, 100, lambda: not GPIO.input(SENS))
    finally:
        GPIO.output(ENA, GPIO.HIGH)

    step_counts = str(steps_till_contact) + ' steps and ' + str(clear_steps) + ' clear steps and ' + str(backup_steps) +' backup steps'
    if steps_till_contact < max_steps_till_contact:
        message = 'Dispensed after ' + step_counts
        # if 'telegram' in secrets:
        #   telegram.notify(message = message, token = secrets['telegram']['notifier_token'], chat_id = secrets['telegram']['chat_id'])
        print(" ", message)
    else:
        message = 'FAILED after ' + step_counts
        if 'telegram' in secrets:
            telegram.notify(message = message, token = secrets['telegram']['notifier_token'], chat_id = secrets['telegram']['chat_id'])
        print(" ", message)

def main():
    global animation
    try:
        while True:
            drop.fill(color = (255, 0, 0))
            animation = Solid(windows, color = (0, 0, 0))
            wait_to_untrigger()

            drop.fill(color = (255, 255, 255))
            animation.animate()
            animation = SparklePulse(windows, speed = 0.05, color = (70, 0, 255), period = 0.1, min_intensity = 0.1, max_intensity = 0.7)

            wait_to_trigger()

            drop.fill(color = (0, 255, 0))
            play_a_sound()

            dispense()
    except KeyboardInterrupt:
        print("\rExiting...                                                  ")
    finally:
        pixels.fill(color = (0, 0, 0))
        pixels.show()
        if ser != None:
            ser.close()

if __name__ == "__main__":
    main()
