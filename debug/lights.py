import board
import neopixel
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.color import AMBER
pixels = neopixel.NeoPixel(board.D18, 30, auto_write = False)

#animation = Blink(pixels, speed = 0.5, color = (255, 70, 0))
#animation = Pulse(pixels, speed = 0.1, color = AMBER, period = 5)
#animation = Sparkle(pixels, speed = 0.1, color = AMBER, num_sparkles = 5)
#animation = SparklePulse(pixels, speed = 0.1, color = AMBER, period = 5, min_intensity = 0.5, max_intensity = 0.7)
animation = SparklePulse(pixels, speed = 0.05, color = (255, 70, 0), period = 0.1, min_intensity = 0.1, max_intensity = 0.7)
while True:
        animation.animate()
#for i in range(10):
#    pixels[i] = (255, 70, 0)
#pixels.fill((0, 0, 0))
#pixels.show()
