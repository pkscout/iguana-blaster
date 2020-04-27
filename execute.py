import sys

if ( __name__ == "__main__" ):
    try:
        command = sys.argv[1]
    except IndexError:
        command = ''
    if command.lower() == 'record':
        from resources.lib.record import Main
    elif command.lower() == 'server':
        from resources.lib.server import Main
    else:
        from resources.lib.blast import Main
    Main()
