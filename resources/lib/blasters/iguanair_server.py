
import json
try:
    import websocket
    has_websocket = True
except ImportError:
    has_websocket = False



class Blaster:
    def __init__( self, ws_ip='localhost', ws_port='9001', irc='1234' ):
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
