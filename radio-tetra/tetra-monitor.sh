#!/bin/bash

# periodicaly checks if new audio data apers if not, send warning email
# because something probably got wrong
#
# add line into crontab to activate monitoring
# * * * * *     ...PATH.../tetra-monitor.sh

# TODO/FIXME: this monitoring is pretty shit
#  * if finds only dir with current date
#    (problem of new day)
#  * it can be corrupted by invalid config.sh
#    (should send email whenever tetra-check.sh returns nonzero status)
#  * WTF why we are killing tetra.sh, problems with frozing should be reported


ROOT=$(dirname $(dirname $(realpath ${0})))
CFG=${ROOT}/radio-tetra/config.sh
. ${CFG}

# re-send warning every MONITOR_TIME minutes
if [ $(find ${MONITOR_LOCK} -mmin +${MONITOR_TIME_RESEND} | wc -l) -eq 1 ]; then
  rm ${MONITOR_LOCK}
fi

NOW=`date +%F`

# WTF
if [ $(find ${REC_DIR}/${NOW}/ -mmin -$((${MONITOR_TIME} - 1)) | wc -l) -lt 2 ]; then
  killall tetra.sh
  exit 0
fi

if [ $(find ${REC_DIR}/${NOW}/ -mmin -${MONITOR_TIME} | wc -l) -lt 2 ]; then
  if [ -e ${MONITOR_LOCK} ]; then
    exit 0
  fi
   echo "V poslednich ${MONITOR_TIME} minutach se nenahral zadny soubor na tetre.

       Tento e-mail neni nevyzadanym obchodnim sdelenim NSA Litomerice ve smyslu par. 1574 odst. 74c zakona 9914/2013 Sbrm. Pokud jej povazujete za spam, smazte svoji adresu v `hostname`:${CFG}." | mail -s "Petra spadla." ${MONITOR_RECIPIENTS}
  touch ${MONITOR_LOCK}
else
  rm -f ${MONITOR_LOCK}
fi

