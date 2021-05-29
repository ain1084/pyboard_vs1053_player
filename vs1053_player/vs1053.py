from micropython import const
from machine import Pin
import utime

class VS1053:

    class OPERATION:
        READ = const(0x03)
        WRITE = const(0x02)

    class REGISTER:
        MODE = const(0)
        #STATUS = const(1)
        #BASS = const(2)
        CLOCKF = const(3)
        #DECODE_TIME = const(4)
        #AUDATA = const(5)
        WRAM = const(6)
        WRAMADDR = const(7)
        HDAT0 = const(8)
        HDAT1 = const(9)
        #AIADDR = const(10)
        #VOL = const(11)
        #AICTRL0 = const(12)
        #AICTRL1 = const(13)
        #AICTRL2 = const(14)
        #AICTRL3 = const(15)

    class MODE:
        #SDIFF = const(1 << 0)
        #LAYER12 = const(1 << 1)
        RESET = const(1 << 2)
        CANCEL = const(1 << 3)
        #EARSPEAKER_LO = const(1 << 4)
        #TESTS = const(1 << 5)
        #STREAM = const(1 << 6)
        #EARSPEAKER_HI = const(1 << 7)
        #DACT = const(1 << 8)
        #SDIORD = const(1 << 9)
        SDISHARE = const(1 << 10)
        SDINEW = const(1 << 11)
        #ADPCM = const(1 << 12)
        #LINE1 = const(1 << 14)
        #CLK_RANGE = const(1 << 15)

    class WRAM:
        class GPIO:
            GPIO7 = const(1 << 7)
            GPIO6 = const(1 << 6)
            GPIO5 = const(1 << 5)
            GPIO4 = const(1 << 4)
            #GPIO3 = const(1 << 3)
            #GPIO2 = const(1 << 2)
            #GPIO1 = const(1 << 1)
            #GPIO0 = const(1 << 0)

        # X data RAM
        END_FILL_BYTE = const(0x1e06)

        # I/O
        GPIO_DDR = const(0xc017)
        #GPIO_IDAT = const(0xc018)
        #GPIO_ODAT = const(0xc019)
        I2S_CONFIG = const(0xc040)

        class I2S:
            MCLK_ENA = const(1 << 3)
            ENA = const(1 << 2)
            SRATE = const(1 << 0)

    __send_buf = bytearray(32)

    def __wait_dreq(self):
        while self.__dreq.value() == 0:
            pass

    def read_register(self, register_address: int) -> int:
        buf = memoryview(self.__send_buf)
        buf[0] = VS1053.OPERATION.READ
        buf[1] = int(register_address)
        buf[2] = 0x00
        buf[3] = 0x00
        self.__wait_dreq()
        self.__cs.low()
        self.__spi.write_readinto(buf[:4], buf[:4])
        self.__cs.high()
        return (buf[2] << 8) + buf[3]

    def write_register(self, register_address: int, value: int):
        buf = memoryview(self.__send_buf)
        buf[0] = VS1053.OPERATION.WRITE
        buf[1] = int(register_address)
        buf[2] = int(value) >> 8
        buf[3] = int(value) & 0xff
        self.__wait_dreq()
        self.__cs.low()
        self.__spi.write(buf[:4])
        self.__cs.high()

    def write_wram(self, address:int , value: int):
        self.write_register(VS1053.REGISTER.WRAMADDR, address)
        self.write_register(VS1053.REGISTER.WRAM, value)
        if address in self.__wram_restore_on_reset_values:
            self.__wram_restore_on_reset_values[address] = value

    def read_wram(self, address:int) -> int:
        self.write_register(VS1053.REGISTER.WRAMADDR, address)
        return self.read_register(VS1053.REGISTER.WRAM)

    def enable_i2s(self):
        self.write_wram(VS1053.WRAM.GPIO_DDR,
                        VS1053.WRAM.GPIO.GPIO7 | VS1053.WRAM.GPIO.GPIO6 | VS1053.WRAM.GPIO.GPIO5 | VS1053.WRAM.GPIO.GPIO4)
        self.write_wram(VS1053.WRAM.I2S_CONFIG, VS1053.WRAM.I2S.MCLK_ENA | VS1053.WRAM.I2S.ENA)

    def write_data(self, buffer) -> int:
        if len(buffer) > 32:
            raise ValueError("buffer length must be less then 32 bytes.")
        self.__wait_dreq()
        self.__spi.write(buffer)
        return len(buffer)

    def write_fill_bytes(self, buffer, count: int) -> int:
        result = count
        while count != 0:
            length = min(len(buffer), count)
            self.__wait_dreq()
            self.__spi.write(buffer[:length])
            count -= length
        return result

    def write_end_fill(self):
        buf = memoryview(self.__send_buf)
        endFillByte = self.read_wram(VS1053.WRAM.END_FILL_BYTE) & 0xff
        for i in range(len(buf)):
            buf[i] = endFillByte
        self.write_fill_bytes(buf, 2052)
        sci_mode = self.read_register(VS1053.REGISTER.MODE)
        self.write_register(VS1053.REGISTER.MODE, sci_mode | VS1053.MODE.CANCEL)
        for _ in range(2048 / 32):
            self.write_fill_bytes(buf, 32)
            if not (self.read_register(VS1053.REGISTER.MODE) & VS1053.MODE.CANCEL):
                break
        else:
            self.soft_reset()
        if self.read_register(VS1053.REGISTER.HDAT0) != 0x0000 or self.read_register(VS1053.REGISTER.HDAT1) != 0x0000:
            raise RuntimeError("Values for SCI_HDAT0 and SCI_HDAT1 must be 0x0000.")

    def soft_reset(self):
        sci_mode = self.read_register(VS1053.REGISTER.MODE)
        self.write_register(VS1053.REGISTER.MODE, sci_mode | VS1053.MODE.RESET)
        utime.sleep_us(2)
        self.__wait_dreq()
        for address, value in self.__wram_restore_on_reset_values.items():
            self.write_wram(address, value)

    def __init__(self, spi, cs_pin_id, dreq_pin_id):
        self.__spi = spi
        self.__cs = Pin(cs_pin_id, Pin.OUT)
        self.__dreq = Pin(dreq_pin_id, Pin.IN)
        self.__wram_restore_on_reset_values = { VS1053.WRAM.GPIO_DDR: 0, VS1053.WRAM.I2S_CONFIG: 0 }

        self.__spi.init(baudrate=1000000, polarity = 0, phase = 0)
        self.write_register(VS1053.REGISTER.MODE, VS1053.MODE.SDINEW | VS1053.MODE.SDISHARE)
        self.write_register(VS1053.REGISTER.CLOCKF, 0x6000)
        self.__spi.init(baudrate=6000000)
        self.soft_reset()
