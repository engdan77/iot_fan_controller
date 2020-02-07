# Fan control
import fan_control
from mywifi import stop_all_wifi, start_ap, wifi_connect
from myconfig import get_config
import gc

default_config = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': 'true',
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_topic': '/fan_control/temp',
                  'mqtt_username': 'username',
                  'mqtt_password': 'password',
                  'trigger_temp': '28',
                  'override_secs': '10'}


def s():
    stop_all_wifi()
    c = get_config(default_config)
    print('config loaded {}'.format(c))
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    fan_control.start_fan_control(c)
    del c
    gc.collect()


def main():
    # from captive_portal import CaptivePortal
    # portal = CaptivePortal()
    # portal.start()
    pass
