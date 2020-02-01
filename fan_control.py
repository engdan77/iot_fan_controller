import logging
import mypicoweb
import uasyncio as asyncio
import dht
from machine import Pin
from ucollections import deque
import ujson
from mypicoweb import MyPicoWeb


def web_index(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    with open('index.html') as f:
        yield from resp.awrite(f.read())


def web_status(req, resp, **kwargs):
    fan_obj = kwargs.get('fan_obj', None)
    print('*'*30)
    print(req)
    print(resp)
    print(kwargs)
    temp_obj = kwargs.get('temp_obj', None)
    fan_obj = kwargs.get('fan_obj', None)
    yield from mypicoweb.start_response(resp)
    print('parseing query param')
    params = req.qs
    if params == 'state=on':
        print('turn on fan')
        fan_obj.switch_state(True)
    elif params == 'state=off':
        print('turn on fan')
        fan_obj.switch_state(False)
    return_data = {'temp': temp_obj.read(), 'status': fan_obj.state_text, 'params': str(params)}
    print(req)
    yield from resp.awrite(ujson.dumps(return_data))


def web_save(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    print(req)
    yield from resp.awrite('')


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

    @property
    def state_text(self):
        return 'on' if self.state is True else 'off'

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
    fan_obj = MyFan(button=button_obj, temp=temp_obj, event_loop=loop)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    app = MyPicoWeb(__name__, temp_obj=temp_obj, button_obj=button_obj, fan_obj=fan_obj)
    app.add_url_rule('/save', web_save)
    app.add_url_rule('/status', web_status)
    app.add_url_rule('/', web_index)

    loop.create_task(update_temp(temp_obj))
    app.run(host="0.0.0.0", port=80, log=log)
