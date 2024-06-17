import asyncio

from request.request import Request


class PlayQueue:
    def __init__(self):
        self.index: int = 0
        self.playlist: list = []
        self.play_queue: asyncio.Queue = asyncio.Queue()

    async def append(self, request:Request):
        """Add a request to the queue."""
        self.playlist.append(request)
        await self.play_queue.put(request)

    async def get(self):
        """Get the next item from the queue and remove it."""
        return await self.play_queue.get()

    def get_next(self):
        """Get the next item in the queue, but do not remove it."""
        try:
            return self.playlist[self.index + 1]
        except IndexError:
            return None

    def is_empty(self):
        """Checks if the queue is empty."""
        return self.play_queue.empty()
