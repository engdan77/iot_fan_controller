from umqtt.simple2 import MQTTClient


def publish(client='umqtt_client', broker='127.0.0.1', topic='/mytopic/foo', message='', username=None, password=None):
    c = MQTTClient(client, broker, user=username, password=password)
    try:
        c.connect()
    except OSError as e:
        print('unable to connect to mqtt {} with error {}'.format(broker, e))
    else:
        # has to be bytes
        c.publish(str(topic).encode(), str(message).encode())
        c.disconnect()
