rem this tells the IR blaster software where the recording file for analog encoded channels are so it can make sure they're working
IF %2 EQU 1016 ECHO %1 > "C:\CustomApps\iguana-blaster\data\recordingpath-%2.txt"
IF %2 EQU 1020 ECHO %1 > "C:\CustomApps\iguana-blaster\data\recordingpath-%2.txt"
IF %2 GEQ 1100 ECHO %1 > "C:\CustomApps\iguana-blaster\data\recordingpath-%2.txt"