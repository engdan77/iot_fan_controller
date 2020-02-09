import utime
from machine import Pin
import uasyncio as asyncio
from mymqtt import publish


class MyFan:
    def __init__(self,
                 fan_pin=12,
                 led_pin=2,
                 button=None,
                 temp=None,
                 event_loop=None,
                 config=None,
                 wdt=None):
        self.wdt = wdt
        self.fan = Pin(fan_pin, Pin.OUT)
        self.led = Pin(led_pin, Pin.OUT)
        self.led(True)
        self.button = button
        self.state = False
        self.mqtt_enabled = config.get('mqtt_enabled', False)
        self.mqtt_broker = config.get('mqtt_broker', None)
        self.mqtt_topic = config.get('mqtt_topic').encode()
        self.mqtt_username = config.get('mqtt_username', None)
        self.mqtt_password = config.get('mqtt_password', None)
        self.trigger_temp = int(config.get('trigger_temp', 30))
        self.override_secs = int(config.get('override_secs', 60))
        self.last_override = 0
        self.temp = temp
        self.last_major_temp = 0
        self.minor_change = 0.5
        if event_loop:
            event_loop.create_task(self.check_changes())
        if self.mqtt_enabled:
            # publish MQTT if enabled
            publish('fan_control_client',
                    self.mqtt_broker,
                    '/notification/message',
                    'fan_control_started',
                    self.mqtt_username,
                    self.mqtt_password)

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

            current_temp = self.temp.read()
            if abs(current_temp - self.last_major_temp) >= self.minor_change:
                self.last_major_temp = current_temp
                if self.mqtt_enabled:
                    # publish MQTT if enabled
                    print('publishing {} to broker {} topic {}'.format(current_temp, self.mqtt_broker, self.mqtt_topic))
                    publish(b'fan_control_client',
                            self.mqtt_broker,
                            self.mqtt_topic,
                            current_temp,
                            self.mqtt_username,
                            self.mqtt_password)

            if self.temp and not self.in_pause_mode:
                if current_temp >= self.trigger_temp and self.on is False:
                    print('turning on fan due to temp above {}'.format(self.trigger_temp))
                    self.switch_state(True)
                elif current_temp < self.trigger_temp and self.on is True:
                    print('turning off fan due to temp below {}'.format(self.trigger_temp))
                    self.switch_state(False)
            if self.wdt:
                self.wdt.feed()
