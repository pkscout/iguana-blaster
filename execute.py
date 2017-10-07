# *  Credits:
# *
# *  v.1.0.0~beta1
# *  original iguana-blaster code by pkscout

import atexit, argparse, glob, os, subprocess, sys, time
import data.config as config
from ConfigParser import *
from resources.common.xlogger import Logger
from resources.common.fileops import readFile, writeFile, deleteFile

p_folderpath, p_filename = os.path.split( os.path.realpath(__file__) )
lw = Logger( logfile = os.path.join( p_folderpath, 'data', 'logfile.log' ),
             numbackups = config.Get( 'logbackups' ), logdebug = str( config.Get( 'debug' ) ) )

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
        self._send_cmds( self._check_cmd_ignore( self.PRE_CMD ), self.IGNORE_PRECMD_FOR ), self.PRE_LASTUSED_FILE ) )
        if self.ARGS.channel:
            self._send_cmds( self._splitchannel() )
        elif self.ARGS.cmds:
            self._send_cmds( self.ARGS.cmds )
        self._send_cmds( self._check_cmd_ignore( self.POST_CMD, self.IGNORE_POSTCMD_FOR ), self.POST_LASTUSED_FILE ) )
        
                
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
            success, loglines = writeFile ( str( time.time() ), lastused_file )
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
            self.PRE_CMD = config.Get( 'ignore_postcmd_for' )


    def _parse_argv( self ):
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        group.add_argument( "-c", "--channel", help="the channel number" )
        group.add_argument( "-m", "--cmds", help="arbitrary string of commands" )
        parser.add_argument( "-n", "--postchannel", help="the command to send after the channel number" )
        parser.add_argument( "-b", "--precmd", help="the string of commands (separated by pipe) to send before any other commands" )
        parser.add_argument( "-e", "--postcmd", help="the string of commands (separated by pipe) to send after any other commands" )
        parser.add_argument( "-w", "--wait", type=int, help="the amount of time (in seconds) to wait between commands" )
        parser.add_argument( "-a", "--forcepre", help="force pre commands to run no matter what", action="store_true" )
        parser.add_argument( "-o", "--forcepost", help="force post commands to run no matter what", action="store_true" )
        self.ARGS = parser.parse_args()


    def _send_cmds( self, cmd ):
        if not cmd:
            return
        cmds = cmd.split('|')
        for one_cmd in cmds:
            if one_cmd:
                keyfile = os.path.join( self.KEYPATH, one_cmd + config.Get( 'key_ext' ) )
                blast_cmd = '"%s" --send "%s"' % (config.Get( 'path_to_IGC' ), keyfile)
                lw.log( ['sending ' + blast_cmd] )
                try:
                    subprocess.check_output( blast_cmd, shell=True)
                except subprocess.CalledProcessError, e:
                    lw.log( [e] )
            time.sleep( self.WAIT_BETWEEN )


    def _setPID( self ):
        lw.log( ['setting PID file'] )
        success, loglines = writeFile( pid, pidfile )
        lw.log( loglines )        


    def _splitchannel( self ):
        cmd_list = []
        for digit in list( self.ARGS.channel ):
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