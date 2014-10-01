#!/bin/bash

. ./config.sh || exit 1

rm /tmp/tetramon.lock

[ $COUNT = 0 ] && exit
let COUNT=COUNT-1
for i in `seq 0 $COUNT`; do
	rm -f "${FIFODIR}/*"
	mkfifo "${FIFODIR}/floats$i"
	mkfifo "${FIFODIR}/bits$i"
	mkdir -p "$TMPDIR/$i"
done

mkdir "${TGTDIR}"
PID=
start_demod() {
	echo "starting osmo-tetra." >&2
	cd "$OSMODIR"
#	./demod/python/osmosdr-tetra-multidemod.py -a "rtl_tcp=radio-tetra.brm:1234" -L 25e3 -f 424e6 & >&2
	./demod/python/tetra-multidemod-channelizer.py & 2>&1
	PID=$!
}

start_demod

cleanup() {
	kill $PID
	for i in `seq 0 $COUNT`; do
		rm "${FIFODIR}/floats$i"
		rm "${FIFODIR}/bits$i"
	done
	rm -r "${TMPDIR}/*"
}

trap cleanup EXIT
for i in `seq 0 $COUNT`; do
	echo "tetra-rx $i"
	./float_to_bits "${FIFODIR}/floats${i}" "${FIFODIR}/bits${i}" &
#	./tetra-rx "${FIFODIR}/bits${i}" "$TMPDIR/$i" >~/rx-$i.log 2>&1 &
	./tetra-rx "${FIFODIR}/bits${i}" "$TMPDIR/$i" >/dev/null 2>&1 &

done

cd "$CODECDIR"
while true; do
	ps "$PID" >/dev/null || start_demod 

	for i in `find "$TMPDIR" -mmin +1 -type f -name '*.out'`; do
		echo "processing $i"
		d=`dirname "$i"`
		mtime=`stat -c "%Y" "$i"`
		fsize=`stat -c "%s" "$i"`
		if [ $fsize -lt 4096 ]; then
			echo "Skipped $i (${fsize}B)"
			rm "$i"
			rm "${i%%.out}.txt"
			continue;
		fi
		dir=`date --date="@$mtime" "+%Y-%m-%d"` 
		
		gssi=`cat "${i%%.out}.txt"|grep -v 16777215|sort|uniq -c|sort -n|egrep '^[ ]* [0-9]* [0-9][0-9][0-9][0-9]$'|tail -n 1`
		if [ -z "$gssi" ]; then
			issi=`cat "${i%%.out}.txt"|grep -v 16777215|sort|uniq -c|sort -n|tail -n 1`
			ssi="${issi##* }"
		else
			ssi="${gssi##* }"
		fi

		[ -z "$ssi" ] && ssi="unknown"

		#ssi="."
		fn=`date --date="@$mtime" "+%Y-%m-%d_%H-%M-%S"` # if it starts the same second, we don't care
		[ ! -d "${TGTDIR}/${dir}/${ssi}" ] && mkdir -p "${TGTDIR}/${dir}/${ssi}"
		
		./cdecoder "$i" /tmp/traffic.cdata > /dev/null 2>&1
		./sdecoder /tmp/traffic.cdata /tmp/traffic.raw  > /dev/null 2>&1
		sox -r 8000 -e signed -b 16 -c 1 /tmp/traffic.raw "${TGTDIR}/${dir}/${ssi}/${fn}.ogg" > /dev/null 2>&1
		#sox -r 8000 -e signed -b 16 -c 1 /tmp/traffic.raw "${TGTDIR}/${dir}/${ssi}/${fn}.flac" rate 16k > /dev/null 2>&1
		
		mv "${i%%.out}.txt" "${TGTDIR}/${dir}/${ssi}/${fn}.txt"
		echo "created: ${TGTDIR}/${dir}/${ssi}/${fn}"
		length=$(($(stat -c %s /tmp/traffic.raw)/16)) # in [ms]
		/home/tetra/add_group.py -i ${ssi} -t $mtime -l $length
		rm "$i"
	done
	sleep 5s
done

