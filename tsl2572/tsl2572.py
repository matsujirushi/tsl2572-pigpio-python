#!/usr/bin/env python3

import pigpio


class Tsl2572:
    __APERS_VALUES = [0, 1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
    __AGAIN_VALUES = [1, 8, 16, 120]

    def __init__(self, pi: pigpio.pi, i2c_handle: int):
        self.__pigpio = pi
        self.__h = i2c_handle

    def read_enable(self) -> dict:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.ENABLE)

        result = {}
        result["SAI"] = True if data & self.__RegEnableBit.SAI else False
        result["AIEN"] = True if data & self.__RegEnableBit.AIEN else False
        result["WEN"] = True if data & self.__RegEnableBit.WEN else False
        result["AEN"] = True if data & self.__RegEnableBit.AEN else False
        result["PON"] = True if data & self.__RegEnableBit.PON else False

        return result

    def write_enable(self, value: dict):
        data = 0
        data |= self.__RegEnableBit.SAI if value["SAI"] else 0
        data |= self.__RegEnableBit.AIEN if value["AIEN"] else 0
        data |= self.__RegEnableBit.WEN if value["WEN"] else 0
        data |= self.__RegEnableBit.AEN if value["AEN"] else 0
        data |= self.__RegEnableBit.PON if value["PON"] else 0

        self.__i2c_write_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.ENABLE, data)

    def read_als_timing(self) -> float:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.ATIME)

        return (256 - data) * 2.73  # [msec.]

    def write_als_timing(self, value: float) -> float:
        data = (256 - int(value / 2.73))
        if data < 0 or 255 < data:
            raise RuntimeError

        self.__i2c_write_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.ATIME, data)

        return (256 - data) * 2.73  # [msec.]

    def read_wait_time(self, wlong: bool) -> float:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.WTIME)

        if not wlong:
            return (256 - data) * 2.73      # [msec.]
        else:
            return (256 - data) * 2.73 * 12  # [msec.]

    def write_wait_time(self, value: float, wlong: bool) -> float:
        if not wlong:
            data = (256 - int(value / 2.73))
        else:
            data = (256 - int(value / 12 / 2.73))
        if data < 0 or 255 < data:
            raise RuntimeError

        self.__i2c_write_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.WTIME, data)

        if not wlong:
            return (256 - data) * 2.73      # [msec.]
        else:
            return (256 - data) * 2.73 * 12  # [msec.]

    def read_als_interrupt_low_threshold(self) -> int:
        data = self.__i2c_read_16(self.__CommandType.AUTO_INCREMENT, self.__CommandAddress.AILTL)

        return data

    def write_als_interrupt_low_threshold(self, value: int):
        data = value

        self.__i2c_write_16(self.__CommandType.AUTO_INCREMENT, self.__CommandAddress.AILTL, data)

    def read_als_interrupt_high_threshold(self) -> int:
        data = self.__i2c_read_16(self.__CommandType.AUTO_INCREMENT, self.__CommandAddress.AIHTL)

        return data

    def write_als_interrupt_high_threshold(self, value: int):
        data = value

        self.__i2c_write_16(self.__CommandType.AUTO_INCREMENT, self.__CommandAddress.AIHTL, data)

    def read_persistence(self) -> int:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.PERS)

        value = self.__APERS_VALUES[data & 0b0000_1111]

        return value

    def write_persistence(self, value: int):
        data = self.__APERS_VALUES.index(value)

        self.__i2c_write_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.PERS, data)

    def read_config(self) -> dict:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.CONFIG)

        result = {}
        result["AGL"] = True if data & self.__RegConfigBit.AGL else False
        result["WLONG"] = True if data & self.__RegConfigBit.WLONG else False

        return result

    def write_config(self, value: dict):
        data = 0
        data |= self.__RegConfigBit.AGL if value["AGL"] else 0
        data |= self.__RegConfigBit.WLONG if value["WLONG"] else 0

        self.__i2c_write_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.CONFIG, data)

    def read_control(self) -> int:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.CONTROL)

        value = self.__AGAIN_VALUES[data & 0b0000_0011]

        return value

    def write_control(self, value: int):
        data = self.__AGAIN_VALUES.index(value)

        self.__i2c_write_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.CONTROL, data)

    def read_id(self) -> int:
        return self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.ID)

    def read_status(self) -> dict:
        data = self.__i2c_read_8(self.__CommandType.REPEATED_BYTE, self.__CommandAddress.STATUS)

        result = {}
        result["AINT"] = True if data & self.__RegStatusBit.AINT else False
        result["AVALID"] = True if data & self.__RegStatusBit.AVALID else False

        return result

    def read_adc0_data(self) -> int:
        data = self.__i2c_read_16(self.__CommandType.AUTO_INCREMENT, self.__CommandAddress.C0DATA)

        return data

    def read_adc1_data(self) -> int:
        data = self.__i2c_read_16(self.__CommandType.AUTO_INCREMENT, self.__CommandAddress.C1DATA)

        return data

    def __i2c_write_8(self, command_type, command_address, data: int):
        self.__pigpio.i2c_write_byte_data(self.__h, self.__command_code(command_type, command_address), data)

    def __i2c_write_16(self, command_type, command_address, data: int):
        self.__pigpio.i2c_write_word_data(self.__h, self.__command_code(command_type, command_address), data)

    def __i2c_read_8(self, command_type, command_address) -> int:
        return self.__pigpio.i2c_read_byte_data(self.__h, self.__command_code(command_type, command_address))

    def __i2c_read_16(self, command_type, command_address) -> int:
        return self.__pigpio.i2c_read_word_data(self.__h, self.__command_code(command_type, command_address))

    class __CommandType:
        REPEATED_BYTE = 0b00    # Repeated byte protocol transaction
        AUTO_INCREMENT = 0b01   # Auto-increment protocol transaction
        SPECIAL = 0b11          # Special function — See description below

    class __CommandAddress:
        ENABLE = 0x00   # R/W Enables states and interrupts
        ATIME = 0x01    # R/W ALS time
        WTIME = 0x03    # R/W Wait time
        AILTL = 0x04    # R/W ALS interrupt low threshold low byte
        AILTH = 0x05    # R/W ALS interrupt low threshold high byte
        AIHTL = 0x06    # R/W ALS interrupt high threshold low byte
        AIHTH = 0x07    # R/W ALS interrupt high threshold high byte
        PERS = 0x0c     # R/W Interrupt persistence filters
        CONFIG = 0x0d   # R/W Configuration
        CONTROL = 0x0f  # R/W Control register
        ID = 0x12       # R   Device ID
        STATUS = 0x13   # R   Device status
        C0DATA = 0x14   # R   CH0 ADC low data register
        C0DATAH = 0x15  # R   CH0 ADC high data register
        C1DATA = 0x16   # R   CH1 ADC low data register
        C1DATAH = 0x17  # R   CH1 ADC high data register

    class __RegEnableBit:
        SAI = 0b0100_0000   # Sleep after interrupt.
        AIEN = 0b0001_0000  # ALS interrupt mask.
        WEN = 0b0000_1000   # Wait enable.
        AEN = 0b0000_0010   # ALS Enable.
        PON = 0b0000_0001   # Power ON.

    class __RegConfigBit:
        AGL = 0b0000_0100   # ALS gain level.
        WLONG = 0b0000_0010  # Wait Long.

    class __RegStatusBit:
        AINT = 0b0001_0000      # ALS Interrupt.
        AVALID = 0b0000_0001    # ALS Valid.

    @staticmethod
    def __command_code(type_: int, address: int) -> int:
        return 0b1000_0000 | type_ << 5 | address


if __name__ == "__main__":
    pi = pigpio.pi()
    sensor = Tsl2572(pi, pi.i2c_open(1, 0x39))

    print(hex(sensor.read_id()))
    print(sensor.read_enable())
    print(sensor.read_als_timing())
    print(sensor.read_wait_time(False))
    print(sensor.read_als_interrupt_low_threshold())
    print(sensor.read_als_interrupt_high_threshold())
    print(sensor.read_persistence())
    print(sensor.read_config())
    print(sensor.read_control())
    print(sensor.read_status())
    print(sensor.read_adc0_data())
    print(sensor.read_adc1_data())

    pi.stop()
