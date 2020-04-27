#v.2.0.0

import atexit, argparse, glob, os, subprocess, sys, time
import resources.config as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import checkPath, readFile, writeFile, deleteFile
from resources.lib.blasters import IguanaIR, IguanaIR_WebSocket
from resources.lib.dvrs import NextPVR

p_folderpath, p_filename = os.path.split( sys.argv[0] )
logpath = os.path.join( p_folderpath, 'data', 'logs', '' )
checkPath( logpath )
lw = Logger( logfile=os.path.join( logpath, 'client.log' ),
             numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )

def _deletePID():
    success, loglines = deleteFile( pidfile )
    lw.log (loglines )
    lw.log( ['script finished'], 'info' )

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
        lw.log( ['script started'], 'info' )
        self._setPID()
        self._parse_argv()
        self._wait_for_prev_cmd()
        self._init_vars()
        if not self.BLASTER:
            lw.log( ['invalid blaster type configured in settings, quitting'], 'info' )
            return
        if not self.DVR:
            lw.log( ['invalid DVR type configured in settings, quitting'], 'info' )
            return
        if self.ARGS.analogcheck and self.LIVETV_DIR:
            success, loglines = self.DVR.CheckAnalog()
            lw.log( loglines )
            if success:
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
        self.LIVETV_DIR = config.Get( 'livetv_dir' )
        self.BLASTER = self._pick_blaster()
        self.DVR = self._pick_dvr()


    def _parse_argv( self ):
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group( required=True )
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
                             path_to_igc=config.Get( 'path_to_IGC' ), irc=self.IRC, wait_between=self.WAIT_BETWEEN )
        elif blaster_type == 'iguanair-websocket':
            return IguanaIR_WebSocket( ws_ip=config.Get( 'ws_ip' ), ws_port=config.Get( 'ws_port' ), irc=self.IRC )
        else:
            return None


    def _pick_dvr( self ):
        dvr_type = config.Get( 'dvr_type' ).lower()
        if dvr_type == 'nextpvr':
            return NextPVR( channel=self.CHANNEL, config=config, rootpath=p_folderpath )
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
