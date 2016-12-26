#!/bin/bash

if [ $(find /tmp/tetramon.lock -mmin +600 | wc -l) -eq 1 ]; then
  rm /tmp/tetramon.lock
fi

if [ $(find ~/tetra-rec/`date +%F`/ -mmin -20 | wc -l) -lt 2 ]; then
  bash ~/run.sh

  if [ -e /tmp/tetramon.lock ]; then
    exit 0
  fi
  echo "V poslednich 20 minutach se nenahral zadny soubor na tetre. System byl automaticky restartovan.
 
    Tento e-mail neni nevyzadanym obchodnim sdelenim NSA Litomerice ve smyslu par. 1574 odst. 74c zakona 9914/2013 Sbrm. Pokud jej povazujete za spam, smazte svoji adresu v ~/tetra-monitor.sh." | mail -s "Tetra spadla, tetra spadla, kdopak nam ji opravi?" XXX@nsalitomerice.cz
  touch /tmp/tetramon.lock
else
  [ -e /tmp/tetramon.lock ] && rm /tmp/tetramon.lock
fi

