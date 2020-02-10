"""fan_control: project for controlling fan using an MCU"""

__license__ = "MIT"
__version__ = "1.0.1"
__email__ = "daniel@engvalls.eu"

import gc
import logging
import mypicoweb
import uasyncio as asyncio
from mybutton import MyButton, blocking_count_clicks
from myconfig import get_config, save_config
from myfan import MyFan
from mytemp import MyTemp
from mytemp import update_temp
from mywatchdog import WDT
from myled import blink_int
from mywifi import stop_all_wifi, start_ap, wifi_connect
from webresources import web_save, web_status, web_getconfig, web_jquery, web_index
import webrepl


WEBREPL_PASSWORD = 'fan_control'
DEFAULT_CONFIG = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': 'true',
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_topic': '/fan_control/temp',
                  'mqtt_username': 'username',
                  'mqtt_password': 'password',
                  'trigger_temp': '28',
                  'override_secs': '10'}


def start_fan_control(config):
    wdt = WDT(timeout=30)
    loop = asyncio.get_event_loop()
    temp_obj = MyTemp()
    button_obj = MyButton(event_loop=loop)
    fan_obj = MyFan(button=button_obj, temp=temp_obj, event_loop=loop, config=config, wdt=wdt)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    app = mypicoweb.MyPicoWeb(__name__, temp_obj=temp_obj, button_obj=button_obj, fan_obj=fan_obj)
    app.add_url_rule('/save', web_save)
    app.add_url_rule('/status', web_status)
    app.add_url_rule('/getconfig', web_getconfig)
    app.add_url_rule('/jquery.min.js', web_jquery)
    app.add_url_rule('/', web_index)

    gc.collect()
    loop.create_task(update_temp(temp_obj))
    app.run(host="0.0.0.0", port=80, log=log)


def main():
    # check initially how many click
    clicks = blocking_count_clicks(timeout=5)
    if clicks == 1:
        print('reset configuration')
        blink_int(on_time=1000)
        save_config(DEFAULT_CONFIG)
    stop_all_wifi()
    c = get_config(DEFAULT_CONFIG)
    print('config loaded {}'.format(c))
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    if clicks == 2:
        print('starting webrepl using password {}'.format(WEBREPL_PASSWORD))
        blink_int(count=10, on_time=200)
        webrepl.start(8266, password='fan_control')
    else:
        start_fan_control(c)
        del c
        gc.collect()
