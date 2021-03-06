defaults = { 'path_to_IGC': '',
             'ig_sleep': 3,
             'key_ext': '.txt',
             'logbackups': 1,
             'debug': False }


try:
    import data.settings_record as overrides
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
    