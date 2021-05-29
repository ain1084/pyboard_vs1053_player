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

    async def __buffer_write(self) -> int:
        total = 0
        while True:
            if self.__is_continuous_func != None and not self.__is_continuous_func():
                break
            result = await self.__buffer.write(self.__file.readinto)
            if result == 0:
                break
            total += result
        self.__buffer.end()
        return total

    async def __buffer_read(self) -> int:
        total = 0
        while True:
            result = await self.__buffer.read(lambda buffer: self.__vs1053.write_data(buffer[:min(len(buffer), 32)]))
            if result == 0:
                break
            total += result
        self.__vs1053.write_end_fill()
        return total
