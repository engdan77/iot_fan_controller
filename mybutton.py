from ucollections import deque
import uasyncio as asyncio
from machine import Pin


class MyButton:
    def __init__(self, button_pin=14, event_loop=None):
        self.pressed_queue = deque((), 10)
        self.button_pin = button_pin
        if event_loop:
            event_loop.create_task(self.check_presses())

    async def check_presses(self, sleep_ms=100, bounce_ms=1000):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            p = Pin(self.button_pin, Pin.IN, Pin.PULL_UP)
            if bool(p.value()) is False:
                self.pressed_queue.append(True)
                print('button pressed')
                await asyncio.sleep_ms(bounce_ms)

    @property
    def pressed(self):
        try:
            return self.pressed_queue.popleft()
        except (ValueError, IndexError):
            return False
