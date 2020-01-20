defaults = { 'path_to_IGC': 'C:\\Program Files (x86)\\IguanaIR\\igclient.exe',
             'digit_map': {'0':'KEY_0',
                           '1':'KEY_1',
                           '2':'KEY_2',
                           '3':'KEY_3',
                           '4':'KEY_4',
                           '5':'KEY_5',
                           '6':'KEY_6',
                           '7':'KEY_7',
                           '8':'KEY_8',
                           '9':'KEY_9'},
             'irc': '1234',
             'key_ext': '.txt',
             'post_channel': '',
             'pre_cmd': '',
             'post_cmd': '',
             'wait_between': 0.1,
             'ignore_precmd_for': 0,
             'ignore_postcmd_for': 0,
             'livetv_dir': '',
             'livetv_ext': '.ts',
             'analog_alt_check': False,
             'analog_wait': 6,
             'analog_fail_cmds': '',
             'aborttime': 10,
             'logbackups': 1,
             'debug': False }


try:
    import data.settings as overrides
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
    