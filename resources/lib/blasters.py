#v.0.3.0

import os, json, subprocess, time
try:
    import websocket
    has_websocket = True
except ImportError:
    has_websocket = False

class IguanaIR:
    def __init__( self, keypath='', key_ext='.txt', path_to_igc='', irc='1234', wait_between=0.1 ):
        self.KEYEXT = key_ext
        self.KEYPATH = keypath
        self.PATHTOIGC = path_to_igc
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



class IguanaIR_WebSocket:
    def __init__( self, ws_ip='localhost', ws_port='9001', irc='1234' ):
        if has_websocket:
            self.WSCLIENT = websocket.WebSocket()
        self.IRC = irc
        self.WSIP = ws_ip
        self.WSPORT = ws_port


    def SendCommands( self, cmd ):
        loglines = []
        if not cmd:
            loglines.append( 'no commands were available to send' )
            return loglines
        if not has_websocket:
            loglines.append( 'websockets is not installed, this blaster module requires it' )
            return loglines        
        jsondict = { 'id':'1', 'jsonrpc':'2.0', 'blaster':'iguanair', 'irc': self.IRC, 'commands':cmd }
        ws_conn = 'ws://%s:%s' % (self.WSIP, self.WSPORT)
        loglines.append( 'sending %s to %s' % (jsondict, ws_conn) )
        try:
            self.WSCLIENT.connect( ws_conn )
        except ConnectionRefusedError:
            loglines.append( 'connection refused' )
            return loglines
        self.WSCLIENT.send( json.dumps( jsondict ) )
        self.WSCLIENT.close()
        loglines.append( 'commands sent' )
        return loglines


