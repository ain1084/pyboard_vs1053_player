import os
import ure
from machine import SPI
from machine import Pin
import uasyncio as asyncio
import utime
from vs1053_player import VS1053, RingBuffer, PlayTask
from pyb import LED

class TriggerButton:
    def __init__(self, pin_id):
        self.__button = Pin(pin_id, Pin.IN, Pin.PULL_UP)
        self.__prev_value = self.__button.value()

    def is_triggered(self):
        value = self.__button.value()
        result = value ^ self.__prev_value
        self.__prev_value = value
        return result & (value ^ 1)

class FileWithAccessLED:
    def __init__(self, file, led):
        self.__file = file
        self.__led = led

    def readinto(self, buffer):
        self.__led.on()
        result = self.__file.readinto(buffer)
        self.__led.off()
        return result

vs1053 = VS1053(spi=SPI(2), cs_pin_id="Y5", dreq_pin_id="Y4")
vs1053.enable_i2s()
buffer = RingBuffer(1024)
next_button = TriggerButton('X17')      # Pyboard "USB" button
access_led = LED(3)                     # Pyboard Orange LED

def start(dir):
    def generate_file_iterator(dir, extensions):
        regex = ure.compile(r'^.+\.(\w+$)')
        for finfo in os.ilistdir(dir):
            if finfo[1] & 0x8000:
                m = regex.match(finfo[0])
                if m != None and (m.group(1).lower() in extensions):
                    yield dir + os.sep + finfo[0]

    async def play_all(vs1053, buffer, play_files):
        total = 0
        for filename in play_files:
            print(filename)
            file = open(filename, 'rb')
            start = utime.ticks_us()
            size = await PlayTask.play(vs1053, buffer, FileWithAccessLED(file, access_led), lambda: not next_button.is_triggered())
            diff = utime.ticks_diff(utime.ticks_us(), start) / 1000
            print("\tDuration:{0}sec / Average rate:{1}kbps".format(int(diff / 1000),  int(size * 8 / diff)))
            total += size
        return total

    extensions = [ 'mp3', 'aac', 'ogg', 'mp4', 'm4a', 'wma' ]
    file_list = generate_file_iterator(dir, extensions)
    asyncio.run(play_all(vs1053, buffer, file_list))
