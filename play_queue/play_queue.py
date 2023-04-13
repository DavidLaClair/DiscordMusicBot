import asyncio


class PlayQueue:
    def __init__(self):
        self.index = 0
        self.playlist = []
        self.play_queue = asyncio.Queue()

    async def append(self, request):
        self.playlist.append(request)
        await self.play_queue.put(request)

    async def get(self):
        return await self.play_queue.get()

    def get_next(self):
        try:
            return self.playlist[self.index + 1]
        except IndexError:
            return None

    def is_empty(self):
        return self.play_queue.empty()
