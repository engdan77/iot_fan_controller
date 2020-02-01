# Fan control
import network
import ujson
import utime
import fan_control

config_file = 'config.json'

default_config = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': False,
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_username': 'user',
                  'mqtt_password': 'password'}


def stop_all_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    ap = network.WLAN(network.AP_IF)
    ap.active(False)


def start_ap(ssid='fan_control', password='123456789'):
    ap = network.WLAN(network.AP_IF)
    utime.sleep(1)
    ap.active(True)
    ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    print('AP mode started')
    print(ap.ifconfig())
    utime.sleep(1)


def wifi_connect(essid, password):
    connected = False
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(essid, password)
        for i in range(10):
            print('attempt {}'.format(i))
            utime.sleep_ms(500)
            if sta_if.isconnected():
                connected = True
                break
        sta_if.active(False)
    else:
        connected = True
    if connected:
        print('WIFI mode started')
        print('network config:', sta_if.ifconfig())
    return connected


def get_config():
    try:
        c = ujson.loads(open(config_file).read())
    except (OSError, ValueError):
        c = default_config
        open(config_file, 'w').write(ujson.dumps(c))
    return c


def s():
    stop_all_wifi()
    c = get_config()
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