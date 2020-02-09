import gc
from sys import platform

import machine

gc.collect()


class WDT:
    def __init__(self, _id=0, timeout=120, use_rtc_memory=True):
        self._timeout = timeout / 10
        self._counter = 0
        self._timer = machine.Timer(_id)
        self._use_rtc_memory = use_rtc_memory
        self.init()
        try:
            with open("watchdog.txt", "r") as f:
                if f.read() == "True":
                    print("Reset reason: Watchdog")
        except Exception as e:
            print(e)  # file probably just does not exist
        try:
            with open("watchdog.txt", "w") as f:
                f.write("False")
        except Exception as e:
            print("Error saving to file: {!s}".format(e))
            if use_rtc_memory and platform == "esp8266":
                rtc = machine.RTC()
                if rtc.memory() == b"WDT reset":
                    print("Reset reason: Watchdog")
                rtc.memory(b"")

    def _wdt(self, t):
        self._counter += self._timeout
        if self._counter >= self._timeout * 10:
            try:
                with open("watchdog.txt", "w") as f:
                    f.write("True")
            except Exception as e:
                print("Error saving to file: {!s}".format(e))
                if self._use_rtc_memory and platform == "esp8266":
                    rtc = machine.RTC()
                    rtc.memory(b"WDT reset")
            machine.reset()

    def feed(self):
        self._counter = 0

    def init(self, timeout=None):
        timeout = timeout or self._timeout
        self._timeout = timeout
        self._timer.init(period=int(self._timeout * 1000), mode=machine.Timer.PERIODIC, callback=self._wdt)

    def deinit(self):  # will not stop coroutine
        self._timer.deinit()