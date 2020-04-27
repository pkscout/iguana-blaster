#v.2.0.0

import json, os, sys, time
import resources.config_server as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import checkPath
from resources.lib.blasters import IguanaIR
from resources.lib.websocket_server import WebsocketServer

p_folderpath, p_filename = os.path.split( sys.argv[0] )
logpath = os.path.join( p_folderpath, 'data', 'logs', '' )
checkPath( logpath )
lw = Logger( logfile=os.path.join( logpath, 'server.log' ),
             numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )



class Main:
    def __init__( self ):
        lw.log( ['script started'], 'info' )
        self.WAIT_BETWEEN = config.Get( 'wait_between' )
        self.CMDRUNNING = False
        self.SERVER = WebsocketServer( config.Get( 'ws_port' ), host=config.Get( 'ws_ip' ) )
        self.SERVER.set_fn_new_client( self._new_client )
        self.SERVER.set_fn_client_left( self._client_left )
        self.SERVER.set_fn_message_received( self._message_received )
        self.SERVER.run_forever()
        lw.log( ['script finished'], 'info' )


    def _new_client( self, client, server ):
        lw.log( ['Client connected'] )


    def _client_left( self, client, server ):
        lw.log( ['Client disconnected'] )


    def _message_received(self, client, server, message ):
        if len(message) > 200:
            message = message[:200] + '..'
        lw.log( ['Client said: %s' % message] )
        jm = json.loads( message )
        blaster = self._pick_blaster( jm )
        if not blaster:
            lw.log( ['invalid blaster type configured in settings, not sending any commands'] )
        else:
            while self.CMDRUNNING:
               time.sleep( 1 )
               lw.log( ['checking to see if previous command has completed'] )
            self.CMDRUNNING = True
            lw.log( ['sending commands on to %s' % jm.get( 'blaster' )] )
            loglines = blaster.SendCommands( jm.get( 'commands' ) )
            lw.log( loglines )
            self.CMDRUNNING = False


    def _pick_blaster( self, jm ):
        if jm.get( 'blaster' ) == 'iguanair':
            return IguanaIR( keypath=os.path.join( p_folderpath, 'data', 'keys' ), key_ext=config.Get( 'key_ext' ),
                             path_to_igc=config.Get( 'path_to_IGC' ), irc=jm.get( 'irc' ), wait_between=self.WAIT_BETWEEN )
        else:
            return None
