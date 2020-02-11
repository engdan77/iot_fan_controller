import dht
from machine import Pin
import uasyncio as asyncio


class MyTemp:
    def __init__(self, pin=4):
        self.d = dht.DHT22(Pin(pin))
        self.temp = 0

    def refresh(self):
        self.d.measure()
        self.temp = self.d.temperature()

    def read(self):
        return self.temp


async def update_temp(_temp_obj, refresh_interval=4):
    count = 0
    while True:
        await asyncio.sleep(refresh_interval)
        try:
            _temp_obj.refresh()
        except OSError as e:
            print('failed get temp due to {}'.format(e))
        count += 1
        print('Updating temp {} current temp {}'.format(count, _temp_obj.temp))
