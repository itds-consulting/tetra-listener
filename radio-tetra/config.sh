#!/bin/bash

# TETRA listener configuration file

[ -d "$ROOT" ] || (echo "Invalid use of config.sh ROOT must be set by parent script"; exit 1)

# path to OSMO-TETRA reciever
OSMOTETRA_DIR=${ROOT}/osmo-tetra/src
# path to root directory of audio codec binaries
CODEC_DIR=${ROOT}/codec/c-code

# used by monitor (must by run in crontab, see tetra-monitor.sh for details)
MONITOR_LOCK=/tmp/brmtetra-moitor.lock
# if no new audio is decoded for this period of time (minutes), send warning email
MONITOR_TIME=15
# resend monitoring warning every N minutes
MONITOR_TIME_RESEND=30
# whitespace separated list of monitoring recipients
MONITOR_RECIPIENTS=""

# decoder temporary files, fifos etc ...
TMP_DIR=~/tetra-tmp
FIFO_TMP_DIR=${TMP_DIR}/fifo
REC_TMP_DIR=${TMP_DIR}/tetra-raw
# where to store decoded tetra audio files
REC_DIR=~/tetra-rec
# format of audio, use anny of: cdata.bz2, wav, flac, ogg
REC_FORMAT=cdata.bz2
# number of decoded channels
STREAMS=72

TUNE_FREQ=424150e3
TUNE_PPM=1
SAMPLE_RATE=1.8e6
# set gain, comment out for automatic gain setting
TUNE_GAIN=36
# Band width usefull for automatic squelch threshold detection
# values >= 1 are interpreted as a fraction of sample rate.
SIGNAL_DETECTION_BW=0.8
# Therhold level (above detected noise level) for automatic squelching.
SIG_DETECTION_THRESHOLD=6
# arguments for osmo-sdr RX block, use rtl_tcp=<ADDR>:<PORT> for TCP source
OSMO_SDR_ARGS="rtl_tcp=10.34.6.90:1234"

# set to yes to enable debug logging
#DEBUG=yes

# graaaah, workarounds

LD_LIBRARY_PATH=${ROOT}/
PYTHONPATH=${PYTHONPATH}:${ROOT}/osmo-tetra/src/demod

