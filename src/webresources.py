import mypicoweb
import index
import gc
import jquery
import ujson
from myconfig import get_config, save_config
from urltools import query_params_to_dict
from machine import reset


def web_index(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    yield from resp.awrite(index.data())
    gc.collect()


def web_jquery(req, resp, **kwargs):
    gc.collect()
    yield from mypicoweb.start_response(resp)
    yield from resp.awrite(jquery.data())
    gc.collect()


def web_status(req, resp, **kwargs):
    gc.collect()
    temp_obj = kwargs.get('temp_obj', None)
    fan_obj = kwargs.get('fan_obj', None)
    yield from mypicoweb.start_response(resp)
    params = req.qs
    print('parsing query param {}'.format(params))
    command, value = params.split('=') if len(params) > 1 else (None, None)
    if command == 'state':
        fan_obj.pause_temp_check()
        print('turning fan {}'.format(value))
        s = {'on': True, 'off': False}.get(value, None)
        fan_obj.switch_state(s)
    return_data = {'temp': temp_obj.read(), 'status': fan_obj.state_text, 'params': str(params)}
    yield from resp.awrite(ujson.dumps(return_data))


def web_save(req, resp, **kwargs):
    yield from mypicoweb.start_response(resp)
    params = query_params_to_dict(req.qs)
    mqtt_enabled = 'mqtt_enabled' in params
    params['mqtt_enabled'] = mqtt_enabled
    print('saving configuration {}'.format(params))
    save_config(params)
    yield from resp.awrite('''<html>
    <body style="background-color:blue;">
    <centrer><p>Configuration saved, rebooting...</p></center>
    </body>
    </html>''')
    reset()


def web_getconfig(req, resp, **kwargs):
    default_config = kwargs.get('config', None)
    gc.collect()
    yield from mypicoweb.start_response(resp)
    c = get_config(default_config)
    print('config loaded {}'.format(c))
    j = ujson.dumps(c)
    yield from resp.awrite(j)
