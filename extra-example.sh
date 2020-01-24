# change the channel
python3 /config/scripts/iguana-blaster/execute.py -c $1

# open the stream
curl  http://172.16.1.4/0.ts
wait
exit $?