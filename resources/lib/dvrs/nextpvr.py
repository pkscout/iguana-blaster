
import os, re, time
from resources.lib.apis import nextpvr

class DVR:

    def __init__( self, config ):
        """Creates a NextPVR DVR object."""
        self.APICALL = nextpvr.API( config.Get( 'dvr_host' ), config.Get( 'dvr_port' ), config.Get( 'dvr_auth' ), 'tvmaze.integration' )
        self.LOGLINES = []
        self.ANALOGWAIT = config.Get( 'analog_wait')
        self.ANALOGALTCHECK = config.Get( 'analog_alt_check' )
        self.ANALOGTHRESHOLD = config.Get( 'analog_threshold' )


    def CheckAnalog( self, channel ):
        channel_name = self._get_channel_name( channel )
        if self._check_analog( 'livetv', channel_name ):
            return True, self.LOGLINES
        if self._check_analog( 'recording', channel_name ):
            return True, self.LOGLINES
        return False, self.LOGLINES


    def _check_analog( self, check_type, channel_name ):
        time.sleep( self.ANALOGWAIT )
        tv_file = 'nothing.ts'
        self.LOGLINES.append( 'got here with ' + check_type )
        if check_type == 'livetv':
            tv_file = self._get_livetv_path( channel_name )
        elif check_type == 'recording':
            tv_file = self._get_recording_path( channel_name )
        self.LOGLINES.append( 'the file is ' + tv_file )
        if not tv_file:
            self.LOGLINES.append( 'no file returned from NextPVR, that probably means this is not a %s file' % check_type )
            return False
        if not os.path.exists( tv_file ):
            self.LOGLINES.append( 'the file does not exist' )
            return False
        file_size = os.stat( tv_file ).st_size
        self.LOGLINES.append( 'the file has a size of %s' % str( file_size ) )
        if file_size == 0 or (self.ANALOGALTCHECK and file_size < self.ANALOGTHRESHOLD * 1000 ):
            self.LOGLINES.append( 'looks like the analog device is not on' )
            return False
        self.LOGLINES.append( 'finished analog check for %s' % check_type )
        return True


    def _get_channel_name( self, channel ):
        success, loglines, channels = self.APICALL.getChannelList()
        self.LOGLINES.extend( loglines )
        if not success:
            return ''
        for one_channel in channels.get( 'channels', [] ):
            self.LOGLINES.append( 'checking %s against %s'% (str( one_channel.get( 'channelNumber', 0 )  ), str( channel)) )
            if str( channel ) == str( one_channel.get( 'channelNumber', 0 ) ):
                self.LOGLINES.append( 'found matching channel, so channel name is %s' % one_channel.get( 'channelName', '' ) )
                return one_channel.get( 'channelName', '' )
        return ''


    def _get_livetv_path( self, channel_name ):
        success, loglines, status = self.APICALL.getSystemStatus()
        self.LOGLINES.extend( loglines )
        if not success:
            return ''
        for item in status.get( 'status', [] ):
            for one_stream in item.get( 'streams', [] ):
                if one_stream.startswith( 'LIVE&' ) and channel_name in one_stream and channel_name:
                    return re.sub( r'LIVE&', '', one_stream )
        return ''


    def _get_recording_path( self, channel_name ):
        success, loglines, recordings = self.APICALL.getRecordingList( thefilter='recording' )
        self.LOGLINES.extend( loglines )
        if not success:
            return ''
        for recording in recordings.get( 'recordings', [] ):
            if recording.get( 'channel', '' ) == channel_name:
                return recording.get( 'file', '' )
        return ''
    
    
    
    
    
    
    
    
