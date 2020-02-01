# Fan control
import fan_control
from mywifi import stop_all_wifi, start_ap, wifi_connect
from myconfig import get_config

default_config = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_username': 'user',
                  'mqtt_password': 'password'}


def s():
    stop_all_wifi()
    c = get_config(default_config)
    print('config loaded {}'.format(c))
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    fan_control.start_fan_control()


def main():
    # from captive_portal import CaptivePortal
    # portal = CaptivePortal()
    # portal.start()
    pass
