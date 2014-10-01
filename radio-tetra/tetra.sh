#!/bin/bash

# main script, start tetra ?reciever? and demodulator

ROOT=$(dirname $(dirname $(realpath ${0})))

. ${ROOT}/radio-tetra/config.sh || exit 1

# reset monitoring, we are alive and happy, now
rm -f ${MONITOR_LOCK}

! [ "$STREAMS" -gt 0 ] && exit

rm -rf ${FIFO_TMP_DIR}
mkdir -p ${FIFO_TMP_DIR}
for i in `seq 1 $STREAMS`; do
	mkfifo "${FIFO_TMP_DIR}/floats$i"
	mkfifo "${FIFO_TMP_DIR}/bits$i"
	mkdir -p "${REC_TMP_DIR}/$i"
done

mkdir ${REC_DIR}
DEMOD_PID=
start_demod() {
	echo "starting osmo-tetra." >&2
	cd "${OSMOTETRA_DIR}"
#	./demod/python/osmosdr-tetra-multidemod.py -a "rtl_tcp=radio-tetra.brm:1234" -L 25e3 -f 424e6 & >&2
	./demod/python/osmosdr-tetra-multidemod.py & 2>&1
	DEMOD_PID=$!
}

cleanup() {
	kill ${DEMOD_PID}
	rm -rf ${FIFO_TMP_DIR}
}

trap cleanup EXIT
cd "${OSMOTETRA_DIR}"
for i in `seq 1 ${STREAMS}`; do
	echo "tetra-rx ${i}"
	./float_to_bits "${FIFO_TMP_DIR}/floats${i}" "${FIFO_TMP_DIR}/bits${i}" &
	./tetra-rx "${FIFO_TMP_DIR}/bits${i}" "${REC_TMP_DIR}/${i}" >/dev/null 2>&1 &
done

start_demod
while true; do
# FIXME: WTF workaround
	ps "${DEMOD_PID}" >/dev/null || start_demod
	cd "${CODEC_DIR}"

	for i in `find "${REC_TMP_DIR}" -mmin +1 -type f -name '*.out'`; do
		echo "processing ${i}"
		d=`dirname "${i}"`
		mtime=`stat -c "%Y" "$i"`
		fsize=`stat -c "%s" "$i"`
		if [ $fsize -lt 4096 ]; then
			echo "Skipped ${i} (${fsize}B)"
			rm "${i}"
			rm "${i%%.out}.txt"
			continue;
		fi
		dir=`date --date="@${mtime}" "+%Y-%m-%d"`

		gssi=`cat "${i%%.out}.txt"|grep -v 16777215|sort|uniq -c|sort -n|egrep '^[ ]* [0-9]* [0-9][0-9][0-9][0-9]$'|tail -n 1`
		if [ -z "${gssi}" ]; then
			issi=`cat "${i%%.out}.txt"|grep -v 16777215|sort|uniq -c|sort -n|tail -n 1`
			ssi="${issi##* }"
		else
			ssi="${gssi##* }"
		fi

		[ -z "${ssi}" ] && ssi="unknown"

		#ssi="."
		fn=`date --date="@${mtime}" "+%Y-%m-%d_%H-%M-%S"` # if it starts the same second, we don't care
		fpath="${REC_DIR}/${dir}/${ssi}"
		mkdir -p "${fpath}"

		./cdecoder "$i" ${TMP_DIR}/traffic.cdata > /dev/null 2>&1
		./sdecoder ${TMP_DIR}/traffic.cdata ${TMP_DIR}/traffic.raw  > /dev/null 2>&1
		sox -q -r 8000 -e signed -b 16 -c 1 ${TMP_DIR}/traffic.raw "${fpath}/${fn}.${REC_FORMAT}"

		mv "${i%%.out}.txt" "${fpath}/${fn}.txt"
		echo "created: ${fpath}/${fn}"
		length=$(($(stat -c %s ${TMP_DIR}/traffic.raw)/16)) # in [ms]
# WTF, where is the fucking file ???
#		${ROOT}/add_group.py -i ${ssi} -t ${mtime} -l ${length}
		rm "${i}"
	done
	sleep 5s
done

