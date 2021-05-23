import uasyncio as asyncio

class RingBuffer:
    class Pointer:
        def __init__(self, size: int):
            self.__index = 0
            self.__size = size

        def reset(self):
            self.__index = 0

        @micropython.native
        def enumerate(self, func, count: int) -> int:
            offset = 0
            while count != 0:
                request = self.__size - self.__index if self.__index + count >= self.__size else count
                result = func(self.__index, self.__index + request)
                self.__index = (self.__index + result) % self.__size
                count -= result
                offset += result
                if result > request:
                    raise ValueError("Invalid function result. Expect result <= {0}.".format(request))
                elif result != request:
                    break
            return offset

    def __init__(self, size: int, write_threshold: int = 0):
        self.__size = size
        self.__buffer = memoryview(bytearray(size))
        self.__read_pointer = RingBuffer.Pointer(size)
        self.__write_pointer = RingBuffer.Pointer(size)
        self.__readable = asyncio.Event()
        self.__writable = asyncio.Event()
        self.__write_threshold = int(size / 2) if write_threshold == 0 else write_threshold
        self.clear()

    def clear(self):
        self.__used = 0
        self.__is_detected_end = False
        self.__writable.set()
        self.__readable.clear()
        self.__read_pointer.reset()
        self.__write_pointer.reset()

    @micropython.native
    async def read(self, func) -> int:
        await self.__readable.wait()
        result = self.__read_pointer.enumerate(lambda start, end: func(self.__buffer[start:end]), self.__used)
        self.__update_used(-result)
        return result

    @micropython.native
    async def write(self, func) -> int:
        await self.__writable.wait()
        result = self.__write_pointer.enumerate(lambda start, end: func(self.__buffer[start:end]), self.__size - self.__used)
        self.__is_detected_end = result == 0
        self.__update_used(result)
        return result

    def write_end(self):
        self.__is_detected_end = True

    @micropython.native
    def __update_used(self, result: int):
        self.__used += result
        is_writable = self.__size - self.__used >= self.__write_threshold and self.__is_detected_end == False

        if is_writable:
            self.__writable.set()
            self.__readable.clear()
        else:
            self.__readable.set()
            self.__writable.clear()
