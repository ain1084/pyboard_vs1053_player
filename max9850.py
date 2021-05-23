from machine import I2C

i2c = I2C(1, freq=100000)
i2c.writeto(16, b'\x06\x00')    # Clock
i2c.writeto(16, b'\x07\x09')    # Charge pump (12.288MHz = 0x09)
i2c.writeto(16, b'\x0a\x08')    # I2S standard format
i2c.writeto(16, b'\x02\x1c')    # Volume (0x3f:min - 0x00:max)
i2c.writeto(16, b'\x05\xfd')    # DAC on
