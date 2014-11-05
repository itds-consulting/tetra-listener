#!/bin/bash

# TETRA listener configuration file


[ -d "$ROOT" ] || (echo "Invalid use of config.sh ROOT must be set by parent script"; exit 1)

# path to OSMO-TETRA reciever
OSMOTETRA_DIR=${ROOT}/osmo-tetra/src
# path to root directory of audio codec binaries
CODEC_DIR=$ROOT/codec/c-code

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
# format of audio, use anny of: wav, flac, ogg
REC_FORMAT=ogg
# number of decoded channels
STREAMS=72

TUNE_FREQ=424e6
TUNE_PPM=0
# set gain, comment out for automatic gain setting
#TUNE_GAIN=36
# squelch level, ignore channels with low signal (dB)
TUNE_SQUELCH=-56
# arguments for osmo-sdr RX block, use rtl_tcp=<ADDR>:<PORT> for TCP source
TUNE_OSMO_ARGS=""
# automatically tune PPM to selected channel
#AUTO_TUNE_CHANNEL=0

# set to yes to enable debug logging
#DEBUG=yes
# comma separated list of channels for printing signal strenght
DEBUG_CHENNELS_PWR=""

# graaaah, workarounds

LD_LIBRARY_PATH=$ROOT/
PYTHONPATH=$PYTHONPATH:$ROOT/osmo-tetra/src/demod

#LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:/lib
#PYTHONPATH=/usr/local/lib/python2.7/site-packages:/usr/local/lib/python2.7/dist-packages:/usr/local/lib64/python2.7/site-packages:/usr/local/lib64/python2.7
