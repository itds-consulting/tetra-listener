#!/usr/bin/python

import sys
from binman import *
from sds import parsesds

if len(sys.argv) != 2:
    print "Usage: %s <sds in RAW hex format, such as 20:C9:00:00:65:04:9E:FF:FF:F0>" % sys.argv[0]
    sys.exit(2)

bin_stream = bitesFromHex(sys.argv[1])

print "BIN> " + bin_stream

print parsesds(bin_stream, 0, 0, 0, 0, 0)
