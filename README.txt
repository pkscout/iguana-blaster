# iguana-blaster
Python command line tool to blast IR commands via the IguanaWorks igclient

Prerequisites:
A functioning IguanaWorks USB IR Transciever <https://www.iguanaworks.net>
Python 3.6.x or later must be installed (Python 2.7.x may work but has not been tested).

To install download and unzip in any directory.  Then copy the keys-example folder to keys.  This example folder contains the 9 digits and power on key for the Spectrum URC1056A03 remote.  These may work for you.  If not, please see the RECORDINGKEYS.txt file for information on how to create new keys.

The script has a set of default settings described in settings-example.py.  Review that file.  If you want to make changes you can either create a new settings.py file and copy and paste in the things you want to override or copy settings-example.py to settings.py and make changes as needed.  If you're not sure what a setting does even after reading the comments in the settings-example.py file, you can probably leave it at the default.

The script can also check to make sure the encoder has created a file.  To enable this option you need to set the livetv_dir in your settings file.  Right now this is optimized for use the NextPVR.  If first checks the LiveTV folder to see if there is a buffer .ts file (meaning LiveTV tuned properly).  If that fails, it looks for a file that tells the script where the recording file is (see ParallelProcessing.bat for an example of how to create that file with NextPVR) and checks to see if that file exists.  If neither do, it toggles the power on the cable box, waits, and then retunes the channel.

This script can send IR signals to one (or more) of the IR channels on the IquanaWorks USB device. That means by changing the command line options used to change the channel you can control up to 4 external devices.  See A NOTE ABOUT IRC below for details on how to do that.

usage: execute.py [-h] [-c CHANNEL | -m CMDS] [-i IRC] [-n POSTCHANNEL]
                  [-b PRECMD] [-e POSTCMD] [-w WAIT] [-a] [-o] [-g]

optional arguments:
  -h, --help            show this help message and exit
  -c CHANNEL, --channel CHANNEL
                        the channel number
  -m CMDS, --cmds CMDS  arbitrary string of commands
  -i IRC, --irc IRC     the IR channel(s) on which to send the command
  -n POSTCHANNEL, --postchannel POSTCHANNEL
                        the command to send after the channel number
  -b PRECMD, --precmd PRECMD
                        the string of commands (separated by pipe) to send before any other commands
  -e POSTCMD, --postcmd POSTCMD
                        the string of commands (separated by pipe) to send after any other commands
  -w WAIT, --wait WAIT  the amount of time (in seconds) to wait between commands
  -a, --forcepre        force pre commands to run no matter what
  -o, --forcepost       force post commands to run no matter what
  -g, --analogcheck     check the analog encoder file and try channel again if not present

A Note about IRC:
Depending on the Iquana USB blaster you got, you have either 2 or 4 channels available (see https://www.iguanaworks.net/wiki/hardware).  By default this script sends an IR signal on all channels (so you don't have to worry about what version you have or where you plug anything in).  If you're having problems with the IR signal not reaching your device, you might want to tell the script to only use the channel you're using.  To send to channels 1 and 3 you would use --irc 13. For just channel 4 you would use --irc 4.  Or, as mentioned above, you can have different command lines for different devices and control up to 4 devices.

Notes:
If you use a pipe in any command string, you must surround the string with single quotes.
An empty pipe in a command string is interpreted as an extra wait.
-c and -m CANNOT be used together. You will get a command line error if you try.
-n is ignored if you don't use -c
