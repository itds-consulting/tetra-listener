#!/bin/bash

# run TETRA listener in background and only if it is not running

TETRA_BIN=$(dirname $(realpath $0))/tetra.sh

/usr/bin/screen -d -m flock -x -n $TETRA_BIN $TETRA_BIN
