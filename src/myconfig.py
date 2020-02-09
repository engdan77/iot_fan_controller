import ujson


def get_config(input_default_config=None, config_file='config.json'):
    try:
        c = ujson.loads(open(config_file).read())
    except (OSError, ValueError):
        if input_default_config:
            c = input_default_config
            open(config_file, 'w').write(ujson.dumps(c))
        else:
            print('No default config given')
    return c


def save_config(input_config, config_file='config.json'):
    if input_config:
        c = input_config
        open(config_file, 'w').write(ujson.dumps(c))
    else:
        print('No default config given')