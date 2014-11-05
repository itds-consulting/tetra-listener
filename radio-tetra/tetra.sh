#!/bin/bash

# main script, start tetra ?reciever? and demodulator

ROOT=$(dirname $(dirname $(realpath ${0})))

. ${ROOT}/radio-tetra/config.sh || exit 1

# reset monitoring, we are alive and happy, now
rm -f ${MONITOR_LOCK}

! [ "$STREAMS" -gt 0 ] && exit

let STREAMS=STREAMS-1

rm -rf ${FIFO_TMP_DIR}
mkdir -p ${FIFO_TMP_DIR}
for i in `seq 0 $STREAMS`; do
	mkfifo "${FIFO_TMP_DIR}/floats$i"
	mkfifo "${FIFO_TMP_DIR}/bits$i"
	mkdir -p "${REC_TMP_DIR}/$i"
done

mkdir -p ${REC_DIR}
DEMOD_PID=
start_demod() {
	echo "starting osmo-tetra." >&2
	AUTO_TUNE_CHANNEL=${AUTO_TUNE_CHANNEL:+-t ${AUTO_TUNE_CHANNEL}}
	DEBUG=${DEBUG:+-d}
	DEBUG_CHENNELS_PWR=${DEBUG_CHENNELS_PWR:+--debug-channels-pwr ${DEBUG_CHENNELS_PWR}}
	TUNE_PPM=${TUNE_PPM:+-p ${TUNE_PPM}}
	TUNE_GAIN=${TUNE_GAIN:+-g ${TUNE_GAIN}}
	TUNE_OSMO_ARGS=${TUNE_OSMO_ARGS:+-a ${TUNE_OSMO_ARGS}}
	${ROOT}/radio-tetra/tetra_rx_multi.py \
		-f "${TUNE_FREQ}" \
		"${TUNE_PPM}" \
		"${TUNE_GAIN}" \
		-l "${TUNE_SQUELCH}" \
		"${TUNE_OSMO_ARGS}" \
		${AUTO_TUNE_CHANNEL} \
		${DEBUG} \
		${DEBUG_CHENNELS_PWR} \
		-o "file:///${FIFO_TMP_DIR}/bits%d" & 2>&1
	DEMOD_PID=$!
}

cleanup() {
	kill ${DEMOD_PID}
}

trap cleanup EXIT
cd "${OSMOTETRA_DIR}"
#rm -rf ${FIFO_TMP_DIR}
for i in `seq 0 ${STREAMS}`; do
	echo "tetra-rx ${i}"
	#./float_to_bits "${FIFO_TMP_DIR}/floats${i}" "${FIFO_TMP_DIR}/bits${i}" &
	#./tetra-rx "${FIFO_TMP_DIR}/bits${i}" "${REC_TMP_DIR}/${i}" >/dev/null 2>&1 &
	./tetra-rx "${FIFO_TMP_DIR}/bits${i}" "${REC_TMP_DIR}/${i}" >"${FIFO_TMP_DIR}/log${i}.txt" 2>&1 &
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

