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
        sta_if.active(True)
        sta_if.connect(essid, password)
        print('connecting to network..., pause 3 sec')
        utime.sleep(3)
        for i in range(1, 10):
            print('attempt {}'.format(i))
            utime.sleep(1)
            if sta_if.isconnected():
                connected = True
                break
        if not connected:
            sta_if.active(False)
    else:
        connected = True
    if connected:
        utime.sleep(1)
        print('network config:', sta_if.ifconfig())
    return connected
