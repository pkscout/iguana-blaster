# this tells the IR blaster software where the recording file for analog encoded channels are
# so it can make sure they're working

# in this example the file is only created for channels 1016, 1020, and 1100 and up

if [ "$2" -eq "1016" ] || [ "$2" -eq "1020" ] || [ "$2" -ge "1100" ]; then
    echo $1 > /config/scripts/iguana-blaster/data/recordingpath-$2.txt
