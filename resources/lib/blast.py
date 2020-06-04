#v.2.0.0

import atexit, argparse, glob, os, subprocess, sys, time
import resources.config as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import readFile, writeFile, deleteFile
from resources.lib.blasters import *
from resources.lib.dvrs import *

pidfile = ''

def _deletePID( ):
    success, loglines = deleteFile( pidfile )

atexit.register( _deletePID )



class Main:
    def __init__( self, thepath ):
        """Start the IR blaster."""
        self.ROOTFILE = thepath
        self.ROOTPATH = os.path.dirname( thepath )
        self.LW = Logger( logfile=os.path.join(self.ROOTPATH, 'data', 'logs', 'client.log' ),
                          numbackups=config.Get( 'logbackups' ), logdebug=config.Get( 'debug' ) )
        self.LW.log( ['script started'], 'info' )
        self._setPID()
        self._parse_argv()
        self._wait_for_prev_cmd()
        self._init_vars()
        if not self.BLASTER:
            self.LW.log( ['invalid blaster type configured in settings, quitting'], 'info' )
            return
        if not self.DVR:
            self.LW.log( ['invalid DVR type configured in settings, quitting'], 'info' )
            return
        if self.ARGS.analogcheck:
            success, loglines = self.DVR.CheckAnalog( self.CHANNEL )
            self.LW.log( loglines )
            if success:
                self.LW.log( ['analog check verified, everything looks OK', 'script finished'], 'info' )
                return
            self.LW.log( ['analog check failed, sending commands to turn the TV box back on'], 'info' )
            self._send_commands( self.ANALOG_FAIL_CMDS )
        self._send_commands( self._check_cmd_ignore( self.PRE_CMD, self.IGNORE_PRECMD_FOR, self.PRE_LASTUSED_FILE ) )
        if self.CHANNEL:
            self._send_commands( self._splitchannel() )
        elif self.ARGS.cmds:
            self._send_commands( self.ARGS.cmds )
        self._send_commands( self._check_cmd_ignore( self.POST_CMD, self.IGNORE_POSTCMD_FOR, self.POST_LASTUSED_FILE ) )
        if (not self.ARGS.analogcheck) and config.Get( 'analog_check' ):
            if os.name == 'nt':
                py_folder, py_file = os.path.split( sys.executable )
                cmd = [os.path.join( py_folder, 'pythonw.exe' ), self.ROOTFILE, '--analogcheck'] + sys.argv[1:]
                self.LW.log( cmd )
            else:
                cmd = '%s %s --analogcheck %s %s' % (sys.executable, self.ROOTFILE, sys.argv[1], sys.argv[2])
                self.LW.log( [cmd] )
            subprocess.Popen( cmd, shell=True )
        self.LW.log( ['script finished'], 'info' )



    def _check_cmd_ignore( self, cmd, ignore_for, lastused_file ):
        if not cmd:
            if lastused_file == self.PRE_LASTUSED_FILE:
                cmd_type = 'pre'
            else:
                cmd_type = 'post'
            self.LW.log( ['no %s command to check' % cmd_type] )
            return ''
        if ignore_for == 0:
            self.LW.log( ['ignoring the cache time and running command'] )
            return cmd
        if os.path.isfile( lastused_file ):
            exists = True
            loglines, lastused = readFile( lastused_file )
            self.LW.log( loglines )
        else:
            exists = False
        if (not exists) or (time.time() - float( lastused ) > ignore_for*60):
            self.LW.log( ['setting lastused and running command'] )
            success, loglines = writeFile ( str( time.time() ), lastused_file, wtype='w' )
            self.LW.log( loglines )
            return cmd
        self.LW.log( ['ignoring command for now'] )
        return ''


    def _init_vars( self ):
        self.PRE_LASTUSED_FILE = os.path.join( self.ROOTPATH, 'data', 'precmd_lastused.txt' )
        self.POST_LASTUSED_FILE = os.path.join( self.ROOTPATH, 'data', 'postcmd_lastused.txt' )
        self.KEYPATH = os.path.join( self.ROOTPATH, 'data', 'keys' )
        if self.ARGS.precmd:
            self.LW.log( ['overriding default pre command with ' + self.ARGS.precmd] )
            self.PRE_CMD = self.ARGS.precmd
        else:
            self.PRE_CMD = config.Get( 'pre_cmd' )
        if self.ARGS.postcmd:
            self.LW.log( ['overriding default post command with ' + self.ARGS.postcmd] )
            self.POST_CMD = self.ARGS.postcmd
        else:
            self.POST_CMD = config.Get( 'post_cmd' )
        if self.ARGS.wait:
            self.LW.log( ['overriding default wait between with ' + str( self.ARGS.wait )] )
            self.WAIT_BETWEEN = self.ARGS.wait
        else:
            self.WAIT_BETWEEN = config.Get( 'wait_between' )
        if self.ARGS.forcepre:
            self.LW.log( ['overriding default pre command cache time'] )
            self.IGNORE_PRECMD_FOR = 0
        else:
            self.IGNORE_PRECMD_FOR = config.Get( 'ignore_precmd_for' )
        if self.ARGS.forcepost:
            self.LW.log( ['overriding default post command cache time'] )
            self.IGNORE_POSTCMD_FOR = 0
        else:
            self.IGNORE_POSTCMD_FOR = config.Get( 'ignore_postcmd_for' )
        if self.ARGS.irc:
            self.LW.log( ['overriding default IR channel(s) with ' + self.ARGS.irc] )
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
        self.LW.log( ['the channel is ' + self.ARGS.channel] )
        self.LW.log( ['analog check is ' + str(self.ARGS.analogcheck)] )


    def _pick_blaster( self ):
        blaster_type = config.Get( 'blaster_type' ).lower()
        if blaster_type == 'iguanair':
            return iguanair.Blaster( keypath=self.KEYPATH, key_ext=config.Get( 'key_ext' ),
                             path_to_igc=config.Get( 'path_to_IGC' ), irc=self.IRC, wait_between=self.WAIT_BETWEEN )
        elif blaster_type == 'iguanair-server':
            return iguanair_server.Blaster( ws_ip=config.Get( 'ws_ip' ), ws_port=config.Get( 'ws_port' ), irc=self.IRC )
        else:
            return None


    def _pick_dvr( self ):
        dvr_type = config.Get( 'dvr_type' ).lower()
        if dvr_type == 'nextpvr':
            return nextpvr.DVR( config=config )
        else:
            return None


    def _send_commands( self, cmds ):
        self.LW.log( ['sending: %s' % cmds], 'info' )
        loglines = self.BLASTER.SendCommands( cmds )
        self.LW.log( loglines )


    def _setPID( self ):
        self.LW.log( ['setting PID file'] )
        try:
            last_pidfile = glob.glob( os.path.join( self.ROOTPATH, 'data', '*.pid' ) )[-1]
            loglines, prev_pid = readFile( last_pidfile )
            self.LW.log( loglines )
            pid = str( int( prev_pid ) + 1 )
            self.PREVPIDFILE = os.path.join( self.ROOTPATH, 'data', 'iguana-blaster-%s.pid' % prev_pid )
        except IndexError:
            pid = '0'
            self.PREVPIDFILE = os.path.join( self.ROOTPATH, 'data', 'dummy.pid' )
        global pidfile
        pidfile = os.path.join( self.ROOTPATH, 'data', 'iguana-blaster-%s.pid' % pid )
        success, loglines = writeFile( pid, pidfile, wtype='w' )
        self.LW.log( loglines )


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
        while os.path.isfile( self.PREVPIDFILE ):
            time.sleep( 1 )
            if time.time() - basetime > config.Get( 'aborttime' ):
                err_str = 'taking too long for previous process to close - aborting attempt to send IR commands'
                self.LW.log( [err_str] )
                sys.exit( err_str )
