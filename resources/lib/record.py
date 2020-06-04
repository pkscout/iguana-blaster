
import os, subprocess, time
import resources.config_record as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import *



class Main:
    def __init__( self, thepath ):
        """Start process to record IR keys."""
        self.ROOTPATH = os.path.dirname( thepath )
        self.LW = Logger( logfile=os.path.join(self.ROOTPATH, 'data', 'logs', 'record.log' ),
                          numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )
        self.LW.log( ['script started'], 'info' )
        self._init_vars()
        thekey = input( self.DIALOGTEXT )
        while thekey:
            self._capture_ir()
            self._create_key( thekey )
            thekey = input( self.DIALOGTEXT )
        self._cleanup()
        self.LW.log( ['script finished'], 'info' )


    def _capture_ir( self ):
        print( 'waiting for remote command...' )
        cmd = '"%s" --receiver-on --sleep %s > "%s"' % (self.PATHTOIGC, str( self.IGSLEEP ), self.TEMPKEY)
        self.LW.log( ['sending ' + cmd] )
        try:
            subprocess.check_output( cmd, shell=True)
        except subprocess.CalledProcessError as e:
            self.LW.log( [e] )
        time.sleep( self.IGSLEEP )


    def _create_key( self, thekey ):
        loglines, raw_ir = readFile( self.TEMPKEY )
        self.LW.log( loglines )
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
                self.LW.log( loglines )
                self.WROTEKEY = success
            success, loglines = deleteFile( self.TEMPKEY )
            self.LW.log( loglines )


    def _create_key_dir( self, thepath ):
        f_exists, loglines = checkPath( os.path.join( thepath, '' ) )
        self.LW.log (loglines )
        return thepath


    def _cleanup( self ):
        self.LW.log( ['cleaning up before quitting'] )
        if os.path.exists( self.TEMPKEY ):
            success, loglines = deleteFile( self.TEMPKEY )
            self.LW.log( loglines )
        success, loglines = deleteFolder( self.TEMPKEYPATH )
        self.LW.log( loglines )
        if not self.WROTEKEY:
            sucess, loglines = deleteFolder( self.KEYPATH )
            self.LW.log( loglines )


    def _get_igc( self, igc ):
        if igc:
            return osPathFromString( igc )
        elif os.name == 'nt':
            return os.path.join( 'C:', 'Program Files (x86)', 'IguanaIR', 'igclient.exe' )
        else :
            return 'igclient'


    def _init_vars( self ):
        self.TEMPKEYPATH = self._create_key_dir( os.path.join( self.ROOTPATH, 'data', 'tmp' ) )
        self.TEMPKEY = os.path.join( self.TEMPKEYPATH, 'tmp.txt' )
        self.KEYPATH = self._create_key_dir( os.path.join( self.ROOTPATH, 'data', 'keys' ) )
        self.IGSLEEP = config.Get( 'ig_sleep' )
        self.KEYEXT = config.Get( 'key_ext' )
        self.DIALOGTEXT = 'Input key to record (hit enter with no key to exit):'
        self.PATHTOIGC = self._get_igc( config.Get( 'path_to_IGC' ) )
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
