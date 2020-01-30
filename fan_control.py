import logging
import picoweb
import uasyncio as asyncio
import dht
from machine import Pin
from ucollections import deque
import utime
from picoweb import HTTPRequest


class MyPicoWeb(picoweb.WebApp):
    def __init__(self, pkg, routes=None, serve_static=True, temp_obj=None):
        self.temp_obj = temp_obj
        super().__init__(pkg, routes, serve_static)

    def _handle(self, reader, writer):
        if self.debug > 1:
            micropython.mem_info()
        close = True
        req = None
        try:
            request_line = yield from reader.readline()
            if request_line == b"":
                if self.debug >= 0:
                    self.log.error("%s: EOF on request start" % reader)
                yield from writer.aclose()
                return
            req = HTTPRequest()
            request_line = request_line.decode()
            method, path, proto = request_line.split()
            if self.debug >= 0:
                self.log.info('%.3f %s %s "%s %s"' % (utime.time(), req, writer, method, path))
            path = path.split("?", 1)
            qs = ""
            if len(path) > 1:
                qs = path[1]
            path = path[0]
            # Find which mounted subapp (if any) should handle this request
            app = self
            while True:
                found = False
                for subapp in app.mounts:
                    root = subapp.url
                    if path[:len(root)] == root:
                        app = subapp
                        found = True
                        path = path[len(root):]
                        if not path.startswith("/"):
                            path = "/" + path
                        break
                if not found:
                    break
            if not app.inited:
                app.init()
            # Find handler to serve this request in app's url_map
            found = False
            for e in app.url_map:
                pattern = e[0]
                handler = e[1]
                extra = {}
                if len(e) > 2:
                    extra = e[2]

                if path == pattern:
                    found = True
                    break
                elif not isinstance(pattern, str):
                    m = pattern.match(path)
                    if m:
                        req.url_match = m
                        found = True
                        break
            if not found:
                headers_mode = "skip"
            else:
                headers_mode = extra.get("headers", self.headers_mode)

            if headers_mode == "skip":
                while True:
                    l = yield from reader.readline()
                    if l == b"\r\n":
                        break
            elif headers_mode == "parse":
                req.headers = yield from self.parse_headers(reader)
            else:
                assert headers_mode == "leave"

            if found:
                req.method = method
                req.path = path
                req.qs = qs
                req.reader = reader
                # My customization to pass temp object
                close = yield from handler(req, writer, temp_obj=self.temp_obj)
            else:
                yield from start_response(writer, status="404")
                yield from writer.awrite("404\r\n")
        except Exception as e:
            if self.debug >= 0:
                self.log.exc(e, "%.3f %s %s %r" % (utime.time(), req, writer, e))
            yield from self.handle_exc(req, writer, e)

        if close is not False:
            yield from writer.aclose()
        if __debug__ and self.debug > 1:
            self.log.debug("%.3f %s Finished processing request", utime.time(), req)


class MyTemp:
    def __init__(self, pin=4):
        self.d = dht.DHT22(Pin(pin))
        self.temp = 0

    def refresh(self):
        self.d.measure()
        self.temp = self.d.temperature()

    def read(self):
        return self.temp


class MyFan:
    def __init__(self, fan_pin=12, led_pin=2, button=None, temp=None, event_loop=None, trigger_temp=28):
        self.fan = Pin(fan_pin, Pin.OUT)
        self.led = Pin(led_pin, Pin.OUT)
        self.led(True)
        self.button = button
        self.state = False
        self.trigger_temp = trigger_temp
        self.temp = temp
        if event_loop:
            event_loop.create_task(self.check_changes())

    @property
    def on(self):
        return self.state

    def switch_state(self, state=None):
        if state is None:
            self.state = not self.state
        else:
            self.state = state
        print('changing state to {}'.format(self.state))
        self.led(not self.state)
        self.fan(self.state)

    async def check_changes(self, sleep_ms=100, button_time_secs=30):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            if self.button.pressed is True:
                print('switching state to {} due to button pressed, wait {} secs'.format(not self.state, button_time_secs))
                self.switch_state()
                await asyncio.sleep(button_time_secs)
            if self.temp:
                current_temp = self.temp.read()
                if current_temp >= self.trigger_temp and self.on is False:
                    print('turning on fan due to temp above {}'.format(self.trigger_temp))
                    self.switch_state(True)
                elif current_temp < self.trigger_temp and self.on is True:
                    print('turning off fan due to temp below {}'.format(self.trigger_temp))
                    self.switch_state(False)


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


def index(req, resp, **kwargs):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("This is a fan controlling system")


def temp(req, resp, **kwargs):
    temp_obj = kwargs.get('temp_obj', None)
    yield from picoweb.start_response(resp)
    yield from resp.awrite('temp: {}'.format(temp_obj.read()))


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


def start_fan_control():
    loop = asyncio.get_event_loop()
    temp_obj = MyTemp()
    button_obj = MyButton(event_loop=loop)
    MyFan(button=button_obj, temp=temp_obj, event_loop=loop)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    app = MyPicoWeb(__name__, temp_obj=temp_obj)
    app.add_url_rule('/temp', temp, temp='100')
    app.add_url_rule('/', index)

    loop.create_task(update_temp(temp_obj))
    app.run(host="0.0.0.0", port=80, log=log)
