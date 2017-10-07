# path to the IguanaWorks igclient (must use double slashes for directories)
path_to_IGC = 'C:\\Program Files (x86)\\IguanaIR\\igclient.exe'

# this is to map the digits in the channel number to key names in LIRC
digit_map = {'0':'KEY_0',
             '1':'KEY_1',
             '2':'KEY_2',
             '3':'KEY_3',
             '4':'KEY_4',
             '5':'KEY_5',
             '6':'KEY_6',
             '7':'KEY_7',
             '8':'KEY_8',
             '9':'KEY_9'}

# the extension used for the key files (please include the period if using an extension)
key_ext = '.txt'

# a command to send after every channel change
# in case your box requires something like enter to send channel
post_channel = ''

# the string of commands to send before a channel number is sent
# this can be overridden by using -b or --precommand from the command line
pre_cmd = ''

# the string of commands to send after a channel number is sent
# this can be overridden by using -e or --postcommand from the command line
post_cmd = ''

# the amount of time in seconds to wait between commands (and channel digits)
# this can be overridden by using -w or --wait from the command line
wait_between = 0

# allows you to not run pre or post commands for a certain period of time IN MINUTES
# useful if, for instance, you want to send a power on command but then not again for 30 minutes
# should speed up channel changes
# ignore pre command can be overridden using -a or --forcepre from command line
# ignore post command can be overridden using -o or --forcepost from command line
ignore_precmd_for = 0
ignore_postcmd_for = 0

# amount of time to wait in seconds until aborting command attempt
aborttime = 10

#number of logs to keep
logbackups = 0

# for debugging you can get a more verbose log by setting this to True
debug = False