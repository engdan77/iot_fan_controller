import logging
import uasyncio as asyncio
import dht
from machine import Pin
import ujson
import mypicoweb
from mybutton import MyButton
import utime
import gc


def web_index(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    with open('index.html') as f:
        yield from resp.awrite(f.read())
    gc.collect()


def web_status(req, resp, **kwargs):
    gc.collect()
    temp_obj = kwargs.get('temp_obj', None)
    fan_obj = kwargs.get('fan_obj', None)
    yield from mypicoweb.start_response(resp)
    params = req.qs
    print('parsing query param {}'.format(params))
    command, value = params.split('=') if len(params) > 1 else (None, None)
    if command == 'state':
        fan_obj.pause_temp_check()
        print('turning fan {}'.format(value))
        s = {'on': True, 'off': False}.get(value, None)
        fan_obj.switch_state(s)
    return_data = {'temp': temp_obj.read(), 'status': fan_obj.state_text, 'params': str(params)}
    yield from resp.awrite(ujson.dumps(return_data))


def web_getconfig(req, resp, **kwargs):
    pass


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
    def __init__(self, fan_pin=12, led_pin=2, button=None, temp=None, event_loop=None, trigger_temp=28, override_secs=120):
        self.fan = Pin(fan_pin, Pin.OUT)
        self.led = Pin(led_pin, Pin.OUT)
        self.led(True)
        self.button = button
        self.state = False
        self.trigger_temp = trigger_temp
        self.override_secs = override_secs
        self.last_override = 0
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

    def pause_temp_check(self):
        print('update last override')
        self.last_override = utime.time()

    @property
    def in_pause_mode(self):
        return self.last_override > 0 and utime.time() <= self.last_override + self.override_secs

    async def check_changes(self, sleep_ms=500, button_time_secs=1):
        while True:
            await asyncio.sleep_ms(sleep_ms)
            if self.button.pressed is True:
                self.pause_temp_check()
                print('switching state to {} due to button pressed, '
                      'waiting {} secs for further press'.format(not self.state, button_time_secs))
                self.switch_state()
                await asyncio.sleep(button_time_secs)
            if self.temp and not self.in_pause_mode:
                current_temp = self.temp.read()
                if current_temp >= self.trigger_temp and self.on is False:
                    print('turning on fan due to temp above {}'.format(self.trigger_temp))
                    self.switch_state(True)
                elif current_temp < self.trigger_temp and self.on is True:
                    print('turning off fan due to temp below {}'.format(self.trigger_temp))
                    self.switch_state(False)


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

    app = mypicoweb.MyPicoWeb(__name__, temp_obj=temp_obj, button_obj=button_obj, fan_obj=fan_obj)
    app.add_url_rule('/save', web_save)
    app.add_url_rule('/status', web_status)
    app.add_url_rule('/', web_index)

    gc.collect()
    loop.create_task(update_temp(temp_obj))
    app.run(host="0.0.0.0", port=80, log=log)
