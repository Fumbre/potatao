import uasyncio

HEADER_FMT = '<B8s'

class SimpleQueue:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.items = []
        self.evt = uasyncio.Event()

    # get last item
    async def get(self):
        while not self.items:
            await self.evt.wait()
        return self.items.pop(0)

    # append items as much as free space exist
    # and put later items when the space will be free
    def put_nowait(self, item):
        if len(self.items) < self.maxsize:
            self.items.append(item)
            self.evt.set()
        
    def full(self):
        return len(self.items) >= self.maxsize
    
    def task_done(self):
        if not self.items:
            self.evt.clear()