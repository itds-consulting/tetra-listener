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
sleep 2
#rtl_sdr -f 427200e3 -s 1.8e6 -g 36 -d 0 -p 48 - | ./fcl -b localhost -p 3334 -n 72 -s 50 -f "./fir.py 1.8e6 18.5e3 1151 rcos" -c 7,21,31,56,6,8,62,20,22,69,17,27,30,55,32,57,11,61,63,16 -t 1 -i U8 -o /tmp/myout2.ch &
rtl_sdr -f 427200e3 -s 1.8e6 -g 33 -d 0 -p 48 - | ./fcl -b localhost -p 3334 -n 72 -s 50 -f "./fir.py 1.8e6 18.5e3 1151 rcos" -c 7,21,31,56,6,8,62,70,68,69,17,27,30,55,26,18,11,61,12,39 -t 1 -i U8 -o /tmp/myout2.ch &

# 425400e3 21,22,20,28,41,27,29,25,42,40,6,51,26,24,0,7,5,19,23,71,52,1,39,50,34,32,61,44,53,70,31,2,18,60,4,3,33,69,38,68,56,58,48,43,67,62,66,57,30,54,35,45,49,65,64,11,47,10,8,59,63,9,12,15,55,14,13,17,16,46,37,36
# 427200e3 7,21,31,56,6,8,62,20,22,69,17,27,30,55,32,57,11,61,63,16,26,70,18,68,28,12,10,45,67,33,60,34,66,44,46,9,5,50,19,59,35,49,29,58,4,23,25,51,48,54,0,47,64,13,14,71,41,15,1,2,52,53,3,43,42,65,39,40,37,38,24,36


cd ~/tetra-listener/radio-tetra
./tetra.sh &

cd ~/tetra-multiframe-sds/
./sds-parser.py -p /tmp/fifos -c dump.cpdu -l INFO


