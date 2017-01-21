#!/bin/bash

if [ $# -ne 4 ]; then
  echo "Usage: $0 fcl_host fcl_port old_channelizer_string demodulator_offset"
  exit 1
fi

g1=$1
g2=$2
export g1
export g2

dates=""
for i in `seq 0 3`; do
  dates="$dates $HOME/tetra-rec/`date --date "$i days ago" +%F`/unknown/codec/"
done

echo "Obtaining list of sniffed data frames, this may take a while..."
hist=`ls $dates|grep bz2|cut -d o -f 2 | cut -d . -f 1|sort -n|uniq -c|grep -vE "^ +[0-9] "|tr -s " "|cut -d " " -f 3`

function getrange() {
 echo getpwr 3 | nc $g1 $g2 | while read line; do n=`echo $line | cut -d " " -f 1`; if [ $(( ( $n - 1 ) % 3 )) -eq 0 ]; then echo $(( ($n - 1) / 3)) `echo $line | cut -d " " -f 2`; fi;done | cut -d " " -f 2
}

echo -n "FDMA scan..."

meas="`getrange`"
for j in `seq 10 10 100`; do
  meas2="`getrange`"
  meas3=""
  for i in `seq $( echo "$meas" | wc -l ) -1 1`; do
    l1=`echo "$meas" | head -n $i | tail -n 1`
    l2=`echo "$meas2" | head -n $i | tail -n 1`
    meas3="`echo $l1 + $l2 | bc -l`"$'\n'"$meas3"
  done
  meas=`echo "$meas3" | tr -s "\n"`

  sleep 1

  echo -n " $j%..."
done
echo

meas=`echo "$meas" | nl -v 0 | LANG=C sort -nk 2 | cut -f 1 | tr -d " " | tac`

cc=`echo "$3" | tr "," "\n"`

rangestart=0
i=-1

newstr=""
for c in $cc; do
  i=$(( $i + 1 ))
  if echo "$hist" | grep -qE "^$(( $i + $4 ))$"; then
    echo "$c (chan id $i) is OK"
    newstr="$newstr,$c"
    continue
  fi

  echo "$c (chan id $i) is not OK"

  # find first non-sniffed channel
  while true; do
    rangestart=$(( $rangestart + 1 ))
    candidate=`echo "$meas" | head -n $rangestart | tail -n 1`
    if ! echo "$cc" | grep -qE "^$candidate$"; then
      break
    fi
    echo "$candidate has good SNR, but we are already sniffing it"
  done

  echo "chosen $candidate instead."

  newstr="$newstr,$candidate"
done

newstr=${newstr#,}

echo "Old FCL string: $3"
echo "New FCL string: $newstr"
echo "$newstr" > /tmp/tetra.scan
