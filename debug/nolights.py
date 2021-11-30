import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 30, auto_write = False)

pixels.fill((0, 0, 0))
pixels.show()
