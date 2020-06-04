#v.2.0.0

import json, os, sys, time
import resources.config_server as config
from resources.lib.xlogger import Logger
from resources.lib.blasters import *
from resources.lib.websocket_server import WebsocketServer



class Main:
    def __init__( self, thepath ):
        """Start IguanaIR Blaster Server."""
        self.ROOTPATH = os.path.dirname( thepath )
        self.LW = Logger( logfile=os.path.join( self.ROOTPATH, 'data', 'logs', 'server.log' ),
                          numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )
        self.LW.log( ['script started'], 'info' )
        self.WAIT_BETWEEN = config.Get( 'wait_between' )
        self.CMDRUNNING = False
        self.SERVER = WebsocketServer( config.Get( 'ws_port' ), host=config.Get( 'ws_ip' ) )
        self.SERVER.set_fn_new_client( self._new_client )
        self.SERVER.set_fn_client_left( self._client_left )
        self.SERVER.set_fn_message_received( self._message_received )
        self.SERVER.run_forever()
        self.LW.log( ['script finished'], 'info' )


    def _new_client( self, client, server ):
        self.LW.log( ['Client connected'] )


    def _client_left( self, client, server ):
        self.LW.log( ['Client disconnected'] )


    def _message_received(self, client, server, message ):
        if len(message) > 200:
            message = message[:200] + '..'
        self.LW.log( ['Client said: %s' % message] )
        jm = json.loads( message )
        blaster = self._pick_blaster( jm )
        if not blaster:
            self.LW.log( ['invalid blaster type configured in settings, not sending any commands'], 'info' )
        else:
            while self.CMDRUNNING:
               time.sleep( 1 )
               self.LW.log( ['checking to see if previous command has completed'], 'info' )
            self.CMDRUNNING = True
            self.LW.log( ['sending commands on to %s' % jm.get( 'blaster' )], 'info' )
            loglines = blaster.SendCommands( jm.get( 'commands' ) )
            self.LW.log( loglines )
            self.CMDRUNNING = False


    def _pick_blaster( self, jm ):
        if jm.get( 'blaster' ) == 'iguanair':
            return iguanair.Blaster( keypath=os.path.join( self.ROOTPATH, 'data', 'keys' ), key_ext=config.Get( 'key_ext' ),
                             path_to_igc=config.Get( 'path_to_IGC' ), irc=jm.get( 'irc' ), wait_between=self.WAIT_BETWEEN )
        else:
            return None
