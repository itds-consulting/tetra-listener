mkdir -p /tmp/fifos
killall tetra-rx
killall fcl
killall tetra.sh
killall rtl_sdr
killall sds-parser.py python2.7

sleep 1

killall -9 tetra-rx
killall -9 fcl
killall -9 tetra.sh
killall -9 rtl_sdr
killall -9 sds-parser.py python2.7

mkfifo /tmp/sdrpipe /tmp/tunepipe
rm /tmp/wireshark_pcapng*

mkfifo /tmp/myout.ch /tmp/pipe /tmp/myout2.ch /tmp/myout1.ch

cd ~/fcl

rtl_sdr -f 425400e3 -s 1.8e6 -g 49 -d 1 -p 22 - | ./fcl -b localhost -p 3333 -n 72 -s 50 -f "./fir.py 1.8e6 18.5e3 1151 rcos" -c 21,22,20,28,41,51,6,25,52,40 -t 1 -i U8 -o /tmp/myout1.ch &
sleep 1
rtl_sdr -f 427200e3 -s 1.8e6 -g 33 -d 0 -p 48 - | ./fcl -b localhost -p 3334 -n 72 -s 50 -f "./fir.py 1.8e6 18.5e3 1151 rcos" -c 7,21,31,56,6,8,62,70,68,69,17,27,30,55,26,18,11,61,12,39 -t 1 -i U8 -o /tmp/myout2.ch &


cd ~/tetra-listener/radio-tetra
./tetra.sh &

cd ~/tetra-multiframe-sds/
./sds-parser.py -p /tmp/fifos -c dump.cpdu -l INFO


