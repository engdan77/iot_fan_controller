"""fan_control: project for controlling fan using an MCU"""

__license__ = "MIT"
__version__ = "1.0.1"
__email__ = "daniel@engvalls.eu"

import gc
import logging
import mypicoweb
import uasyncio as asyncio
from mybutton import MyButton
from myconfig import get_config
from myfan import MyFan
from mytemp import MyTemp
from mytemp import update_temp
from mywatchdog import WDT
from mywifi import stop_all_wifi, start_ap, wifi_connect
from webresources import web_save, web_status, web_getconfig, web_jquery, web_index

default_config = {'essid': 'MYWIFI',
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
    stop_all_wifi()
    c = get_config(default_config)
    print('config loaded {}'.format(c))
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    start_fan_control(c)
    del c
    gc.collect()
