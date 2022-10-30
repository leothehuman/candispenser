import serial

ser = serial.Serial("/dev/ttyS0", 115200)
if ser.is_open == False:
    ser.open()

def measureLidar():
    global ser
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
                print(distance, ", ", strength, ", ", temperature/8 - 256)
                return distance

def main():
    try:
        while 1:
            measureLidar()
    finally:
        if ser != None:
            ser.close()

main()
