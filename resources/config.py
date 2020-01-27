defaults = { 'blaster_type': 'iguanair',
             'dvr_type': 'nextpvr',
             'path_to_IGC': '',
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
             'key_ext': '.txt',
             'wait_between': 0.1,
             'irc': '1234',
             'post_channel': '',
             'pre_cmd': '',
             'post_cmd': '',
             'ignore_precmd_for': 0,
             'ignore_postcmd_for': 0,
             'livetv_dir': '',
             'livetv_ext': '.ts',
             'analog_alt_check': False,
             'analog_threshold': 1024,
             'analog_wait': 6,
             'analog_fail_cmds': '',
             'aborttime': 10,
             'ws_ip': 'localhost',
             'ws_port': 9001,
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
    