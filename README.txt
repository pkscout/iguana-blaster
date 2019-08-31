# iguana-blaster
Python command line tool to blast IR commands via the IguanaWorks igclient

Prerequisites:
A functioning IguanaWorks USB IR Transciever <https://www.iguanaworks.net>
Python 2.7.x must be installed (Python 3.x may work but has not been tested).

To install download and unzip in any directory.  Then copy the keys-example folder to keys.  This example folder contains the 9 digits and power on key for the Spectrum URC1056A03 remote.  These may work for you.  If not, please see the RECORDINGKEYS.txt file for information on how to create new keys.

The script has a set of default settings described in settings-example.py.  Review that file.  If you want to make changes you can either create a new settings.py file and copy and paste in the things you want to override or copy settings-example.py to settings.py and make changes as needed.  If you're not sure what a setting does even after reading the comments in the settings-example.py file, you can probably leave it at the default.

The script will also check to make sure the encoder has created a file.  Right now this is optimized for use the NextPVR.  If first checks the LiveTV folder to see if there is a buffer .ts file (meaning LiveTV tuned properly).  If that fails, it looks for a file that tells the script where the recording file is (see ParallelProcessing.bat for an example of how to create that file with NextPVR) and checks to see if that file exists.  If neither do, it toggles the power on the cable box, waits, and then retunes the channel.

Usage: execute.py [-h] [-c CHANNEL | -m 'CMDS'] [-n 'POSTCHANNEL'] [-b 'PRECMD']
                  [-e 'POSTCMD'] [-w WAIT] [-a] [-o]

Optional arguments:
  -h, --help                show this help message and exit
  -c CHANNEL, --channel CHANNEL
                            the channel number
  -m 'CMDS', --cmds 'CMDS'  arbitrary string of commands (separated by pipe)
  -n 'POSTCHANNEL', --postchannel 'POSTCHANNEL'
                            the command to send after the channel number
  -b 'PRECMD', --precmd 'PRECMD'
                            the string of commands (separated by pipe) to send
                            before any other commands
  -e 'POSTCMD', --postcmd 'POSTCMD'
                            the string of commands (separated by pipe) to send
                            after any other commands
  -w WAIT, --wait WAIT      the amount of time (in seconds) to wait between
                            commands
  -a, --forcepre            force pre commands to run no matter what
  -o, --forcepost           force post commands to run no matter what

Notes:
If you use a pipe in any command string, you must surround the string with single quotes.
An empty pipe in a command string is interpreted as an extra wait.
-c and -m CANNOT be used together. You will get a command line error if you try.
-n is ignored if you don't use -c