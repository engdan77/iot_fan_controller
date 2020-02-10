from machine import Pin
from ucollections import deque
import uasyncio as asyncio
import utime
from myled import blink_int


class MyButton:
    def __init__(self, button_pin=14, event_loop=None):
        self.pressed_queue = deque((), 10)
        self.button_pin = button_pin
        if event_loop:
            event_loop.create_task(self.check_presses())

    async def check_presses(self, sleep_ms=300, bounce_ms=1000):
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


def blocking_count_clicks(button_pin=14, timeout=5, debounce_ms=5, sleep_ms=10):
    press_count = 0
    number_iterations = (timeout * 1000) / sleep_ms
    for _ in range(number_iterations):
        p = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        if bool(p.value()) is False:
            being_pressed = []
            for d in range(20):
                being_pressed.append(bool(p.value()))
                utime.sleep_ms(debounce_ms)
            if not any(being_pressed):
                blink_int()
                press_count += 1
                print('button pressed')
        utime.sleep_ms(sleep_ms)
    return press_count
