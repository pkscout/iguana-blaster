# *  Credits:
# *
# *  v.1.3.0
# *  original iguana-blaster code by pkscout

import atexit, argparse, glob, os, subprocess, sys, time
import resources.config as config
from resources.lib.xlogger import Logger
from resources.lib.fileops import checkPath, readFile, writeFile, deleteFile
from configparser import *
if config.Get( 'analog_alt_check' ):
    try:
        import cv2
        gen_thumbs = True
    except ImportError:
        lw.log( ['cv2 not installed, disabling alternative video check'] )
        gen_thumbs = False

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
        if self.ARGS.analogcheck and self.LIVETV_DIR:
            if self._check_analog( 'livetv' ):
                return
            if self._check_analog( 'recording' ):
                return
            self._send_cmds( self.ANALOG_FAIL_CMDS )
        self._send_cmds( self._check_cmd_ignore( self.PRE_CMD, self.IGNORE_PRECMD_FOR, self.PRE_LASTUSED_FILE ) )
        if self.CHANNEL:
            self._send_cmds( self._splitchannel() )
        elif self.ARGS.cmds:
            self._send_cmds( self.ARGS.cmds )
        self._send_cmds( self._check_cmd_ignore( self.POST_CMD, self.IGNORE_POSTCMD_FOR, self.POST_LASTUSED_FILE ) )
        if (not self.ARGS.analogcheck) and self.LIVETV_DIR:
            py_folder, py_file = os.path.split( sys.executable )
            cmd = [os.path.join( py_folder, 'pythonw.exe' ), os.path.join(p_folderpath, p_filename), '--analogcheck'] + sys.argv[1:]
            lw.log( cmd )
            subprocess.Popen( cmd, shell=True )
        

    def _check_analog( self, type ):
        # give the recording a chance to start
        time.sleep( self.ANALOG_WAIT )
        tv_file = 'nothing.ts'
        lw.log( ['got here with ' + type] )
        if type == 'livetv':
            try:
                files = os.listdir( self.LIVETV_DIR )
            except FileNotFoundError:
                files = []
            for name in files:
                if name.endswith( config.Get( 'livetv_ext' ) ):
                    tv_file = os.path.join( self.LIVETV_DIR, name )
                    break
        elif type == 'recording':
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
        if os.stat( tv_file ).st_size == 0:
            lw.log( ['the file %s has a zero size' % tv_file] )
            return False
        lw.log( ['the file %s has a non zero size' % tv_file] )
        if config.Get( 'analog_alt_check' ) and gen_thumbs:
            threshold = config.Get( 'analog_threshold' )
            lw.log( ['checking video stream by comparing two image snapshots'] )
            image1 = self._get_image( tv_file )
            image2 = self._get_image( tv_file, get_last=True )
            lw.log( ['have two potential images to check'] )
            lw.log( ['checking the difference between the two images'] )
            difference = cv2.subtract( image1, image2 )
            blue, green, red = cv2.split( difference )
            blue_diff = cv2.countNonZero( blue )
            green_diff = cv2.countNonZero( green )
            red_diff = cv2.countNonZero( red )
            lw.log( ['got blue diff of %s, green diff of %s, and red diff of %s' % (str( blue_diff ), str( green_diff ), str( red_diff ))] )
            if blue_diff <= threshold and green_diff <= threshold and red_diff <= threshold:
                lw.log( ['the images are the same, the source is not transmitting'] )
                return False
            else:
                lw.log( ['the images are different, the source is transmitting'] )                    
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


    def _convert_irc_to_hex( self, irc ):
        channels = list( str( irc ) )
        lw.log( ['the list of IR channels is:'] )
        lw.log( channels )
        total = 0
        for channel in channels:
            if channel == '3':
                total = total + 4
            elif channel == '4':
                total = total + 8
            else:
                total = total + int( channel )
        return str( hex( total ) )


    def _get_image( self, videopath, get_last=False ):
        image = None
        vidcap = cv2.VideoCapture( videopath )
        num_frames = int( vidcap.get( cv2.CAP_PROP_FRAME_COUNT ) )
        fps = int( vidcap.get( cv2.CAP_PROP_FPS ) )
        lw.log( ['got numframes: %s and fps: %s' % (str( num_frames ), str( fps ))] )
        if num_frames < 30 and fps < 30:
            lw.log( ['probably an error when reading file with opencv, skipping thumbnail generation'] )
            return None
        if get_last:
            if fps > num_frames:
                frame_cap = num_frames
            else:
                frame_cap = num_frames - fps
            thumbpath = os.path.join( p_folderpath, 'data', 'secondimage.jpg' )
        else:
            if fps > num_frames:
                frame_cap = 1
            else:
                frame_cap = fps
            thumbpath = os.path.join( p_folderpath, 'data', 'firstimage.jpg' )
        lw.log( ['capturing frame %s' % str( frame_cap )] )
        vidcap.set( cv2.CAP_PROP_POS_FRAMES,frame_cap )
        success, image = vidcap.read()
        if success:
            success, buffer = cv2.imencode(".jpg", image)
            if success:
                success, loglines = writeFile( buffer, thumbpath, wtype='wb' )
                lw.log( loglines )
                image = cv2.imread( thumbpath )
            else:
                lw.log( ['unable to encode thumbnail'] )
        else:
            lw.log( ['unable to create thumnail: frame out of range'] )
        return image


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
            self.IRC = self._convert_irc_to_hex( self.ARGS.irc )
        else:
            self.IRC = self._convert_irc_to_hex( config.Get( 'irc' ) )
        lw.log( ['the hex IRC channel is ' + self.IRC] )
        self.CHANNEL = self.ARGS.channel.strip()
        self.ANALOG_FAIL_CMDS = config.Get( 'analog_fail_cmds' )
        self.ANALOG_WAIT = config.Get( 'analog_wait' )
        self.LIVETV_DIR = config.Get( 'livetv_dir' )


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


    def _send_cmds( self, cmd ):
        if not cmd:
            return
        cmds = cmd.split('|')
        for one_cmd in cmds:
            if one_cmd:
                keyfile = os.path.join( self.KEYPATH, one_cmd + config.Get( 'key_ext' ) )
                blast_cmd = '"%s" --set-channels %s --send "%s"' % (config.Get( 'path_to_IGC' ), self.IRC, keyfile)
                lw.log( ['sending ' + blast_cmd] )
                try:
                    subprocess.check_output( blast_cmd, shell=True)
                except subprocess.CalledProcessError as e:
                    lw.log( [e] )
            time.sleep( self.WAIT_BETWEEN )


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