import uasyncio as asyncio

class PlayTask:
    def __init__(self, vs1053, buffer, file, is_continuous_func):
        self.__vs1053 = vs1053
        self.__buffer = buffer
        self.__file = file
        self.__buffer.clear()
        self.__is_continuous_func = is_continuous_func

    async def play(vs1053, buffer, file, is_continuous_func = None) -> int:
        t = PlayTask(vs1053, buffer, file, is_continuous_func)
        result = await asyncio.gather(*(t.__buffer_write(), t.__buffer_read()))
        return result[1]    # Return total bytes of read

    async def __buffer_write(self):
        total = 0
        result = 0
        file = self.__file
        buffer = self.__buffer
        is_continuous_func = self.__is_continuous_func
        while True:
            if is_continuous_func != None and not is_continuous_func():
                buffer.write_end()
                result = 0
            else:
                result = await buffer.write(file.readinto)
            total += result
            if result == 0:
                break
        return total

    async def __buffer_read(self):
        total = 0
        buffer = self.__buffer
        while True:
            result = await buffer.read(self.__vs1053_write_data)
            total += result
            if result == 0:
                break

        self.__vs1053.write_end_fill()
        return total

    def __vs1053_write_data(self, buffer):
        count = min(len(buffer), 32)
        self.__vs1053.write_data(buffer[0:count])
        return count
