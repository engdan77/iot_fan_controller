# Fan control
import network
import ujson
import utime
import gc

config_file = 'config.json'

default_config = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': False,
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_username': 'user',
                  'mqtt_password': 'password'}


def start_ap(ssid='fan_control', password='123456789'):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)
    print(ap.ifconfig())


def wifi_connect(essid, password):
    connected = False
    sta_if = network.WLAN(network.STA_IF)
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
    if connected:
        print('network config:', sta_if.ifconfig())
    return connected


def get_config():
    try:
        c = ujson.loads(open(config_file).read())
    except OSError:
        c = default_config
        open(config_file, 'w').write(ujson.dumps(c))
    return c


def s():
    c = get_config()
    print('config loaded {}'.format(c))
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    print(locals())
    print(globals())
    print(gc.mem_free())
    gc.collect()
    import fan_control


def main():
    # from captive_portal import CaptivePortal
    # portal = CaptivePortal()
    # portal.start()
    pass
