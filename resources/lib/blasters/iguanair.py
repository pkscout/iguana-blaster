
import os, subprocess, time
from resources.lib.fileops import osPathFromString


class Blaster:
    def __init__( self, keypath='', key_ext='.txt', path_to_igc='', irc='1234', wait_between=0.1 ):
        self.KEYEXT = key_ext
        self.KEYPATH = keypath
        self.PATHTOIGC = self._get_igc( path_to_igc )
        self.IRC = self._convert_irc_to_hex( irc )
        self.WAITBETWEEN = wait_between


    def SendCommands( self, cmd ):
        loglines = []
        if not cmd:
            loglines.append( 'no commands were available to send' )
            return loglines
        cmds = cmd.split('|')
        for one_cmd in cmds:
            if one_cmd:
                keyfile = os.path.join( self.KEYPATH, one_cmd + self.KEYEXT )
                blast_cmd = '"%s" --set-channels %s --send "%s"' % (self.PATHTOIGC, self.IRC, keyfile)
                loglines.append( 'sending ' + blast_cmd )
                try:
                    subprocess.check_output( blast_cmd, shell=True)
                except subprocess.CalledProcessError as e:
                    loglines.append( e )
            time.sleep( self.WAITBETWEEN )
        return loglines


    def _convert_irc_to_hex( self, irc ):
        channels = list( str( irc ) )
        total = 0
        for channel in channels:
            if channel == '3':
                total = total + 4
            elif channel == '4':
                total = total + 8
            else:
                total = total + int( channel )
        return str( hex( total ) )


    def _get_igc( self, igc ):
        if igc:
            return osPathFromString( igc )
        elif os.name == 'nt':
            return os.path.join( 'C:', 'Program Files (x86)', 'IguanaIR', 'igclient.exe' )
        else :
            return 'igclient'
