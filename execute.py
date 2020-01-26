# *  Credits:
# *
# *  v.2.0.0
# *  original iguana-blaster code by pkscout

import atexit, argparse, glob, os, subprocess, sys, time
import resources.config as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import readFile, writeFile, deleteFile
from resources.lib.blasters import IguanaIR, IguanaIR_WebSocket

p_folderpath, p_filename = os.path.split( os.path.realpath(__file__) )
lw = Logger( logfile=os.path.join( p_folderpath, 'data', 'logfile.log' ),
             numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )

def _deletePID():
    success, loglines = deleteFile( pidfile )
    lw.log (loglines )

try:
    last_pidfile = glob.glob( os.path.join( p_folderpath, 'data', '*.pid' ) )[-1]
    loglines, prev_pid = readFile( last_pidfile )
    pid = str( int( prev_pid ) + 1 )
    prev_pidfile = os.path.join( p_folderpath, 'data', 'iguana-blaster-%s.pid' % prev_pid )
except IndexError:
    pid = '0'
    prev_pidfile = os.path.join( p_folderpath, 'data', 'dummy.pid' )
pidfile = os.path.join( p_folderpath, 'data', 'iguana-blaster-%s.pid' % pid )
atexit.register( _deletePID )


class Main:
    def __init__( self ):
        self._setPID()
        self._parse_argv()
        self._wait_for_prev_cmd()
        self._init_vars()
        if not self.BLASTER:
            lw.log( ['no valid blaster type configured in settings, quitting'] )
            return
        if self.ARGS.analogcheck and self.LIVETV_DIR:
            if self._check_analog( 'livetv' ):
                return
            if self._check_analog( 'recording' ):
                return
            self._send_commands( self.ANALOG_FAIL_CMDS )
        self._send_commands( self._check_cmd_ignore( self.PRE_CMD, self.IGNORE_PRECMD_FOR, self.PRE_LASTUSED_FILE ) )
        if self.CHANNEL:
            self._send_commands( self._splitchannel() )
        elif self.ARGS.cmds:
            self._send_commands( self.ARGS.cmds )
        self._send_commands( self._check_cmd_ignore( self.POST_CMD, self.IGNORE_POSTCMD_FOR, self.POST_LASTUSED_FILE ) )
        if (not self.ARGS.analogcheck) and self.LIVETV_DIR:
            if os.name == 'nt':
                py_folder, py_file = os.path.split( sys.executable )
                cmd = [os.path.join( py_folder, 'pythonw.exe' ), os.path.join(p_folderpath, p_filename), '--analogcheck'] + sys.argv[1:]
                lw.log( cmd )
            else:
                cmd = '%s %s --analogcheck %s %s' % (sys.executable, os.path.join(p_folderpath, p_filename), sys.argv[1], sys.argv[2])
                lw.log( [cmd] )
            subprocess.Popen( cmd, shell=True )

    def _check_analog( self, check_type ):
        # give the recording a chance to start
        time.sleep( self.ANALOG_WAIT )
        tv_file = 'nothing.ts'
        lw.log( ['got here with ' + check_type] )
        if check_type == 'livetv':
            if os.path.exists( self.LIVETV_DIR ):
                files = os.listdir( self.LIVETV_DIR )
            else:
                files = []
            for name in files:
                if name.endswith( config.Get( 'livetv_ext' ) ):
                    tv_file = os.path.join( self.LIVETV_DIR, name )
                    break
        elif check_type == 'recording':
            recordingrefpath = os.path.join( p_folderpath, 'data', 'recordingpath-%s.txt' % self.CHANNEL )
            loglines, recordingfile = readFile( recordingrefpath )
            lw.log( loglines )
            success, loglines = deleteFile( recordingrefpath )
            lw.log( loglines )
            if recordingfile:
                lw.log( ['coverting string %s to path' % recordingfile] )
                temp = recordingfile.strip()
                lw.log(['put string %s into temporary variable' % temp] )
                if temp.startswith('"') and temp.endswith('"'):
                    tv_file = temp[1:-1]
        lw.log( ['the file is ' + tv_file] )
        if not os.path.exists( tv_file ):
            lw.log( ['the file %s does not exist' % tv_file] )
            return False
        lw.log( ['the file %s exists' % tv_file] )
        file_size = os.stat( tv_file ).st_size
        lw.log( ['the file %s has a size of %s' % (tv_file, str( file_size ))] )
        if file_size == 0 or (config.Get( 'analog_alt_check' ) and file_size < config.Get( 'analog_threshold' ) * 1000 ):
            lw.log( ['looks like the analog device is not on'] )
            return False
        lw.log( ['finished analog check'] )
        return True


    def _check_cmd_ignore( self, cmd, ignore_for, lastused_file ):
        if not cmd:
            if lastused_file == self.PRE_LASTUSED_FILE:
                cmd_type = 'pre'
            else:
                cmd_type = 'post'
            lw.log( ['no %s command to check' % cmd_type] )
            return ''
        if ignore_for == 0:
            lw.log( ['ignoring the cache time and running command'] )
            return cmd
        if os.path.isfile( lastused_file ):
            exists = True
            loglines, lastused = readFile( lastused_file )
            lw.log( loglines )
        else:
            exists = False
        if (not exists) or (time.time() - float( lastused ) > ignore_for*60):
            lw.log( ['setting lastused and running command'] )
            success, loglines = writeFile ( str( time.time() ), lastused_file, wtype='w' )
            lw.log( loglines )
            return cmd
        lw.log( ['ignoring command for now'] )
        return ''


    def _get_igc( self ):
        igc = config.Get( 'path_to_IGC' )
        if igc:
            return igc
        elif os.name == 'nt':
            return 'C:\\Program Files (x86)\\IguanaIR\\igclient.exe'
        else:
            return 'igclient'


    def _init_vars( self ):
        self.PRE_LASTUSED_FILE = os.path.join( p_folderpath, 'data', 'precmd_lastused.txt' )
        self.POST_LASTUSED_FILE = os.path.join( p_folderpath, 'data', 'postcmd_lastused.txt' )
        self.KEYPATH = os.path.join( p_folderpath, 'data', 'keys' )
        if self.ARGS.precmd:
            lw.log( ['overriding default pre command with ' + self.ARGS.precmd] )
            self.PRE_CMD = self.ARGS.precmd
        else:
            self.PRE_CMD = config.Get( 'pre_cmd' )
        if self.ARGS.postcmd:
            lw.log( ['overriding default post command with ' + self.ARGS.postcmd] )
            self.POST_CMD = self.ARGS.postcmd
        else:
            self.POST_CMD = config.Get( 'post_cmd' )
        if self.ARGS.wait:
            lw.log( ['overriding default wait between with ' + str( self.ARGS.wait )] )
            self.WAIT_BETWEEN = self.ARGS.wait
        else:
            self.WAIT_BETWEEN = config.Get( 'wait_between' )
        if self.ARGS.forcepre:
            lw.log( ['overriding default pre command cache time'] )
            self.IGNORE_PRECMD_FOR = 0
        else:
            self.IGNORE_PRECMD_FOR = config.Get( 'ignore_precmd_for' )
        if self.ARGS.forcepost:
            lw.log( ['overriding default post command cache time'] )
            self.IGNORE_POSTCMD_FOR = 0
        else:
            self.IGNORE_POSTCMD_FOR = config.Get( 'ignore_postcmd_for' )
        if self.ARGS.irc:
            lw.log( ['overriding default IR channel(s) with ' + self.ARGS.irc] )
            self.IRC = self.ARGS.irc
        else:
            self.IRC = config.Get( 'irc' )
        self.CHANNEL = self.ARGS.channel.strip()
        self.ANALOG_FAIL_CMDS = config.Get( 'analog_fail_cmds' )
        self.ANALOG_WAIT = config.Get( 'analog_wait' )
        self.LIVETV_DIR = config.Get( 'livetv_dir' )
        self.BLASTER = self._pick_blaster()


    def _parse_argv( self ):
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        group.add_argument( "-c", "--channel", help="the channel number" )
        group.add_argument( "-m", "--cmds", help="arbitrary string of commands" )
        parser.add_argument("-i", "--irc", help="the IR channel(s) on which to send the command")
        parser.add_argument( "-n", "--postchannel", help="the command to send after the channel number" )
        parser.add_argument( "-b", "--precmd", help="the string of commands (separated by pipe) to send before any other commands" )
        parser.add_argument( "-e", "--postcmd", help="the string of commands (separated by pipe) to send after any other commands" )
        parser.add_argument( "-w", "--wait", type=int, help="the amount of time (in seconds) to wait between commands" )
        parser.add_argument( "-a", "--forcepre", help="force pre commands to run no matter what", action="store_true" )
        parser.add_argument( "-o", "--forcepost", help="force post commands to run no matter what", action="store_true" )
        parser.add_argument( "-g", "--analogcheck", help="check the analog encoder file and try channel again if not present", action="store_true" )
        self.ARGS = parser.parse_args()
        lw.log( ['the channel is ' + self.ARGS.channel] )
        lw.log( ['analog check is ' + str(self.ARGS.analogcheck)] )


    def _pick_blaster( self ):
        blaster_type = config.Get( 'blaster_type' ).lower()
        if blaster_type == 'iguanair':
            return IguanaIR( keypath=self.KEYPATH, key_ext=config.Get( 'key_ext' ),
                             path_to_igc=self._get_igc(), irc=self.IRC, wait_between=self.WAIT_BETWEEN )
        elif blaster_type == 'iguanair-websocket':
            return IguanaIR_WebSocket( ws_ip=config.Get( 'ws_ip' ), ws_port=config.Get( 'ws_port' ), irc=self.IRC )
        else:
            return None


    def _send_commands( self, cmds ):
        loglines = self.BLASTER.SendCommands( cmds )
        lw.log( loglines )


    def _setPID( self ):
        lw.log( ['setting PID file'] )
        success, loglines = writeFile( pid, pidfile, wtype='w' )
        lw.log( loglines )


    def _splitchannel( self ):
        cmd_list = []
        for digit in list( self.CHANNEL ):
            try:
                blast_digit = config.Get( 'digit_map' )[digit]
            except IndexError:
                blast_digit = ''
            if blast_digit:
                cmd_list.append( blast_digit )
        if config.Get( 'post_channel' ):
            cmd_list.append( config.Get( 'post_channel' ) )
        return "|".join( list( cmd_list ) )


    def _wait_for_prev_cmd( self ):
        basetime = time.time()
        while os.path.isfile( prev_pidfile ):
            time.sleep( 1 )
            if time.time() - basetime > config.Get( 'aborttime' ):
                err_str = 'taking too long for previous process to close - aborting attempt to send IR commands'
                lw.log( [err_str] )
                sys.exit( err_str )



if ( __name__ == "__main__" ):
    lw.log( ['script started'], 'info' )
    Main()
lw.log( ['script finished'], 'info' )