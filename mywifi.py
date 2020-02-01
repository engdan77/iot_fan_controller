import network
import utime


def stop_all_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    ap = network.WLAN(network.AP_IF)
    ap.active(False)


def start_ap(ssid='fan_control'):
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
