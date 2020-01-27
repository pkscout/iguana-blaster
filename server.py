# *  Credits:
# *
# *  v.2.0.0
# *  original iguana-blaster code by pkscout
# *  websocket server code by Johan Hanssen Seferidis
# *  available at https://github.com/Pithikos/python-websocket-server

import json, os
import resources.config_server as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import checkPath
from resources.lib.blasters import IguanaIR
from resources.lib.websocket_server import WebsocketServer

p_folderpath, p_filename = os.path.split( os.path.realpath(__file__) )
checkPath( os.path.join( p_folderpath, 'data', 'logs', '' ) )
lw = Logger( logfile=os.path.join( p_folderpath, 'data', 'logs', 'server.log' ),
             numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )


class Main:
    def __init__( self ):
        self.WAIT_BETWEEN = config.Get( 'wait_between' )
        self.SERVER = WebsocketServer( config.Get( 'ws_port' ), host=config.Get( 'ws_ip' ) )
        self.SERVER.set_fn_new_client( self._new_client )
        self.SERVER.set_fn_client_left( self._client_left )
        self.SERVER.set_fn_message_received( self._message_received )
        self.SERVER.run_forever()


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
            lw.log( ['no valid blaster type configured in settings, not sending any commands'] )
        else:
            lw.log( ['sending commands on to %s' % jm.get( 'blaster' )] )
            loglines = blaster.SendCommands( jm.get( 'commands' ) )
            lw.log( loglines )


    def _get_igc( self ):
        igc = config.Get( 'path_to_IGC' )
        if igc:
            return igc
        elif os.name == 'nt':
            return 'C:\\Program Files (x86)\\IguanaIR\\igclient.exe'
        else:
            return 'igclient'


    def _pick_blaster( self, jm ):
        if jm.get( 'blaster' ) == 'iguanair':
            return IguanaIR( keypath=os.path.join( p_folderpath, 'data', 'keys' ), key_ext=config.Get( 'key_ext' ),
                             path_to_igc=self._get_igc(), irc=jm.get( 'irc' ), wait_between=self.WAIT_BETWEEN )
        else:
            return None



if ( __name__ == "__main__" ):
    lw.log( ['script started'], 'info' )
    Main()
lw.log( ['script finished'], 'info' )