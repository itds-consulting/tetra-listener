#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: $0 codec_directory_to_prune"
  exit 1
fi

cd "$1"

ndel=0
prev=`ls -1 *.cdata.bz2|wc -l`

for f in *.cdata.bz2; do
  [ -e "$f" ] || continue
  [ `du -b "$f" | cut -f 1` -lt 1024 ] && continue

  d=`echo "$f" | cut -d "_" -f 1,2 | sed -re "s/(.{9})_(..)-(..)-(..)/\1 \2:\3:\4/"`
  s=`date --date "$d" +%s`

  for f2 in $( ls `date --date @$s "+%F_%H-%M-%S"`*.cdata.bz2 ) $( ls `date --date @$(( $s + 1 )) "+%F_%H-%M-%S"`*.cdata.bz2 2>/dev/null ); do
    [ "$f2" = "$f" ] && continue

    bzcat "$f"  | hexdump -ve '16/1 "%02X " "\n"' | tr -d " \n" | fold -w 138 > /tmp/f1
    bzcat "$f2" | hexdump -ve '16/1 "%02X " "\n"' | tr -d " \n" | fold -w 138 > /tmp/f2

    l1=`cat /tmp/f1 | wc -l`
    l2=`cat /tmp/f2 | wc -l`

    maxl=$l1
    minl=$l2
    if [ $l2 -gt $l1 ]; then
      maxl=$l2
      minl=$l1
    fi

    delta=$(( $l1 * 10 - $l2 * 10 ))
    [ ${delta/#-/} -ge $minl ] && continue

    ndiff=`diff /tmp/f1 /tmp/f2 | wc -l`

    #echo $f $f2   $minl $ndiff

    if [ $(( $ndiff * 5 )) -ge $minl ]; then
      #echo "$f and $f2 differ"
      continue
    fi

    #echo "$f and $f2 are the same"
    if [ $l2 -gt $l1 ]; then
      rm $f
    else
      rm $f2
    fi
    ndel=$(( $ndel + 1 ))
    break

  done
done

echo "Removed $ndel ($(( $ndel * 100 / $prev ))%) duplicates"
