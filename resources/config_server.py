defaults = { 'path_to_IGC': 'C:\\Program Files (x86)\\IguanaIR\\igclient.exe',
             'key_ext': '.txt',
             'wait_between': 0.1,
             'ws_ip': '0.0.0.0',
             'ws_port': 9001,
             'logbackups': 1,
             'debug': False }


try:
    import data.settings_server as overrides
    has_overrides = True
except ImportError:
    has_overrides = False


def Reload():
    if has_overrides:
        reload( overrides )


def Get( name ):
    setting = None
    if has_overrides:
        setting = getattr(overrides, name, None)
    if not setting:
        setting = defaults.get( name, None )
    return setting
    