#!/bin/bash

if [ $(find /tmp/tetramon.lock -mmin +300 | wc -l) -eq 1 ]; then
  rm /tmp/tetramon.lock
fi

if [ $(find /home/tetra-mount/tetra-wav/`date +%F`/ -mmin -13 | wc -l) -lt 2 ]; then
  killall tetra.sh
  exit 0
fi

if [ $(find /home/tetra-mount/tetra-wav/`date +%F`/ -mmin -15 | wc -l) -lt 2 ]; then
  if [ -e /tmp/tetramon.lock ]; then
    exit 0
  fi
  echo "V poslednich 15 minutach se nenahral zadny soubor na tetre.
 
    Tento e-mail neni nevyzadanym obchodnim sdelenim NSA Litomerice ve smyslu par. 1574 odst. 74c zakona 9914/2013 Sbrm. Pokud jej povazujete za spam, smazte svoji adresu v krakenko:/home/tetra/tetra-monitor.sh." | mail -s "Spadla tetra" jenda@hrach.eu mrkva@mrkva.eu pasky@ucw.cz tomsuch@tomsuch.net
  touch /tmp/tetramon.lock
else
  [ -e /tmp/tetramon.lock ] && rm /tmp/tetramon.lock
fi

