def unquote(string):
    """unquote('abc%20def') -> b'abc def'."""
    _hextobyte_cache = {}
    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        return b''
    if isinstance(string, str):
        string = string.encode('utf-8')
    bits = string.split(b'%')
    if len(bits) == 1:
        return string
    res = [bits[0]]
    append = res.append
    for item in bits[1:]:
        try:
            code = item[:2]
            char = _hextobyte_cache.get(code)
            if char is None:
                char = _hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)
    return b''.join(res)


def query_params_to_dict(input_params):
    params = {x[0]: unquote(x[1])
              for x in
              [x.split("=") for x in input_params.split("&")]
              }
    return params
