#!/bin/bash

if ! ps x|grep -q [S]CREEN; then
  /usr/bin/screen -d -m /home/tetra/tetra.sh
fi

