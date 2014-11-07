#!/usr/bin/python3

"""Print out channels power level in dB.

Usage: tetra_cli_pwr.py [CH_NO [CH_NO [CH_NO ...]]]"""

from xmlrpc import client
import sys

c = client.Server("http://localhost:60200")
if len(sys.argv) > 1:
    pwr = c.get_channels_pwr([int(ch) for ch in sys.argv[1:]])
else:
    pwr = c.get_channels_pwr()
pwr.sort(reverse=True)
for p in pwr:
    print(p)

