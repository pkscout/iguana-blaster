#v.1.0.0

import os, time
from resources.lib.fileops import readFile, deleteFile

class NextPVR:
    def __init__( self, channel, config, rootpath ):
        self.LOGLINES = []
        self.ROOTPATH = rootpath
        self.CHANNEL = channel
        self.ANALOGWAIT = config.Get( 'analog_wait')
        self.LIVETVDIR = config.Get( 'livetv_dir' )
        self.LIVETVEXT = config.Get( 'livetv_ext' )
        self.ANALOGALTCHECK = config.Get( 'analog_alt_check' )
        self.ANALOGTHRESHOLD = config.Get( 'analog_threshold' )


    def CheckAnalog( self ):
        if self._check_analog( 'livetv' ):
            return True, self.LOGLINES
        if self._check_analog( 'recording' ):
            return True, self.LOGLINES
        return False, self.LOGLINES


    def _check_analog( self, check_type ):
        time.sleep( self.ANALOGWAIT )
        tv_file = 'nothing.ts'
        self.LOGLINES.append( 'got here with ' + check_type )
        if check_type == 'livetv':
            if os.path.exists( self.LIVETVDIR ):
                files = os.listdir( self.LIVETVDIR )
            else:
                files = []
            for name in files:
                if name.endswith( self.LIVETVEXT ):
                    tv_file = os.path.join( self.LIVETVDIR, name )
                    break
        elif check_type == 'recording':
            recordingrefpath = os.path.join( self.ROOTPATH, 'data', 'recordingpath-%s.txt' % self.CHANNEL )
            loglines, recordingfile = readFile( recordingrefpath )
            self.LOGLINES.extend( loglines )
            success, loglines = deleteFile( recordingrefpath )
            self.LOGLINES.extend( loglines )
            if recordingfile:
                self.LOGLINES.append( 'coverting string %s to path' % recordingfile )
                temp = recordingfile.strip()
                self.LOGLINES.append( 'put string %s into temporary variable' % temp )
                if temp.startswith('"') and temp.endswith('"'):
                    tv_file = temp[1:-1]
        self.LOGLINES.append( 'the file is ' + tv_file )
        if not os.path.exists( tv_file ):
            self.LOGLINES.append( 'the file %s does not exist' % tv_file )
            return False
        self.LOGLINES.append( 'the file %s exists' % tv_file )
        file_size = os.stat( tv_file ).st_size
        lw.log( ['the file %s has a size of %s' % (tv_file, str( file_size ))] )
        if file_size == 0 or (self.ANALOGALTCHECK and file_size < self.ANALOGTHRESHOLD * 1000 ):
            self.LOGLINES.append( 'looks like the analog device is not on' )
            return False
        self.LOGLINES.append( 'finished analog check for %s' % check_type )
        return True
