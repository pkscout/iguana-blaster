# *  Credits:
# *
# *  v.2.2.0
# *  original iguana-blaster code by pkscout

import os, subprocess, time
import resources.config_record as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import checkPath, readFile, deleteFile, writeFile, deleteFolder

p_folderpath, p_filename = os.path.split( os.path.realpath(__file__) )
checkPath( os.path.join( p_folderpath, 'data', 'logs', '' ) )
lw = Logger( logfile=os.path.join( p_folderpath, 'data', 'logs', 'record.log' ),
             numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )


class Main:
    def __init__( self ):
        self._init_vars()
        thekey = input( self.DIALOGTEXT )
        while thekey:
            self._capture_ir()
            self._create_key( thekey )
            thekey = input( self.DIALOGTEXT )
        self._cleanup()


    def _capture_ir( self ):
        print( 'waiting for remote command...' )
        cmd = '"%s" --receiver-on --sleep %s > "%s"' % (self.PATHTOIGC, str( self.IGSLEEP ), self.TEMPKEY)
        lw.log( ['sending ' + cmd] )
        try:
            subprocess.check_output( cmd, shell=True)
        except subprocess.CalledProcessError as e:
            lw.log( [e] )
        time.sleep( self.IGSLEEP )


    def _create_key( self, thekey ):
        loglines, raw_ir = readFile( self.TEMPKEY )
        lw.log( loglines )
        if raw_ir:
            first_pulse = False
            ir_cmd = []
            for one_line in raw_ir.splitlines():
                one_line = one_line.strip().replace( ':', '' )
                if not first_pulse:
                    if one_line.startswith( 'pulse' ):
                        first_pulse = True
                        ir_cmd.append( one_line )
                else:
                    if self._long_space( one_line ):
                        break
                    elif one_line.startswith( 'space' ) or one_line.startswith( 'pulse' ):
                        ir_cmd.append( one_line )
            if ir_cmd:
                success, loglines = writeFile( "\n".join( ir_cmd ), os.path.join( self.KEYPATH, 'KEY_%s%s' % (thekey, self.KEYEXT) ), wtype='w' )
                lw.log( loglines )
                self.WROTEKEY = success
            success, loglines = deleteFile( self.TEMPKEY )
            lw.log( loglines )


    def _create_key_dir( self, thepath ):
        f_exists, loglines = checkPath( os.path.join( thepath, '' ) )
        lw.log (loglines )
        return thepath


    def _cleanup( self ):
        lw.log( ['cleaning up before quitting'] )
        if os.path.exists( self.TEMPKEY ):
            success, loglines = deleteFile( self.TEMPKEY )
            lw.log( loglines )
        success, loglines = deleteFolder( self.TEMPKEYPATH )
        lw.log( loglines )
        if not self.WROTEKEY:
            sucess, loglines = deleteFolder( self.KEYPATH )
            lw.log( loglines )


    def _get_igc( self ):
        igc = config.Get( 'path_to_IGC' )
        if igc:
            return igc
        elif os.name == 'nt':
            return 'C:\\Program Files (x86)\\IguanaIR\\igclient.exe'
        else:
            return 'igclient'


    def _init_vars( self ):
        self.TEMPKEYPATH = self._create_key_dir( os.path.join( p_folderpath, 'data', 'tmp' ) )
        self.TEMPKEY = os.path.join( self.TEMPKEYPATH, 'tmp.txt' )
        self.KEYPATH = self._create_key_dir( os.path.join( p_folderpath, 'data', 'keys' ) )
        self.IGSLEEP = config.Get( 'ig_sleep' )
        self.KEYEXT = config.Get( 'key_ext' )
        self.DIALOGTEXT = 'Input key to record (hit enter with no key to exit):'
        self.PATHTOIGC = self._get_igc()
        self.WROTEKEY = False


    def _long_space( self, one_line ):
        line_list = one_line.split( ' ' )
        try:
            thetype = line_list[0]
            thevalue = line_list[1]
        except IndexError:
            thetype = ''
            thevalue = ''
        if thetype.lower() == 'space':
            try:
                value_int = int( thevalue.strip() )
            except ValueError:
                return False
            if value_int > 20000:
                return True
            else:
                return False
        else:
            return False



if ( __name__ == "__main__" ):
    lw.log( ['script started'], 'info' )
    Main()
lw.log( ['script finished'], 'info' )