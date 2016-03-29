#!/usr/bin/python

import subprocess
import sys
from Queue import Queue, Empty
from threading import Thread, Lock
import getopt
import os
import time
import struct
import sqlite3 as lite
import signal

from binman import *
from multiframe import *
from sds import parsesds
from dbo import create_schema

from libdeka import setloglevel, mylog as l
from fragtype import Fragtype
from cpdu import CPDU, pdu2string
from pcap import pcap_header

from config import *


def dkinit(arfcn, timeslot, multiframes):
    """ Create empty list on a given arfcn and timeslot """
    if not (arfcn, timeslot) in multiframes.keys():
        multiframes[(arfcn, timeslot)] = []


"""Dictionary of pending multiframes.
The keys are tuples of (ARFCN, TIMESLOT).
The values are lists of CPDU objects."""
mlock = Lock()
multiframes = {}


def tshark_in_thr(tshark_filter, pcapq):
    """ Thread that feeds tshark from pcapq """
    tshark_filter.stdin.write(pcap_header)
    if dumppcap:
        dumppcap.write(pcap_header)
    while True:
        msg = pcapq.get()
        tshark_filter.stdin.write(msg)
        if dumppcap:
            dumppcap.write(msg)


def tshark_out_thr(tshark_filter, pduq):
    """ Thread that reads CPDUs from tshark and puts them to pduq """
    while True:
        line = tshark_filter.stdout.readline()
        if not line:
            break
        pduq.put(line.strip())
        if dumpcpdu:
            dumpcpdu.write(line)
        tshark_filter.stdout.flush()
    l("tshark died!", "CRIT")


def pcap_in_thr(path, q):
    """ Thread that reads packets from path and stuffs them into q """
    f = open(path, "rb")
    data = ""
    while True:
        newdata = f.read(1024)
        if not newdata:
            break
        data += newdata
        hlen = 4 * 4
        while len(data) >= hlen:
            hdr = data[:hlen]
            ret = struct.unpack('4I', hdr)
            assert ret[2] == ret[3], "pcap packet truncate %X %X %X %X" % (ret[0], ret[1], ret[2], ret[3])
            size = ret[2] + hlen

            if len(data) > size:
                packet = data[:size]
                q.put(packet)
                data = data[size:]
            else:
                break
    l("Read for pipe %s died" % path, "CRIT")


def stdin_thr(q):
    """ Thread that reads CPDUs from stdin """
    while True:
        line = sys.stdin.readline()
        if not line:
            sys.exit(0)
        q.put(line.strip())


def gc_thr(mq, mlock):
    """ Garbage collector, eats orphaned unfinished multiframes. """
    while True:
        time.sleep(5)
        mlock.acquire()
        cutoff = time.time() - multiframe_tx_interval
        for item in mq.keys():
            if mq[item] and mq[item] != []:
                child = mq[item][0]
                if child.time < cutoff:
                    l("Sacrifice child with %i frames, arfcn=%i, ts=%i" % (len(item), child.arfcn, child.timeslot),
                      "INFO")
                    for frm in mq[item]:
                        s = pdu2string(frm)
                        l("Lost: " + s, "DBG")
                    mq[item] = []
        mlock.release()


""" *** Main program *** """

""" Parse command-line options """
try:
    opts, args = getopt.getopt(sys.argv[1:], "p:c:r:l:")
except getopt.GetoptError:
    print "Usage: %s [-p pcap_dir] [-c dump.cpdu] [-r dump.pcap] [-l loglevel]" % sys.argv[0]
    print " -p pcap_dir       read packets from directory"
    print " -c dump.cpdu      save decoded CPDUs to file"
    print " -r dump.pcap      generate packet capture of the entire network"
    print " -l loglevel       loglevel: DBG, SDS, INFO, WARN, CRIT"
    sys.exit(2)

pcapdir = None
dumpcpdu = None
dumppcap = None
for opt, arg in opts:
    if opt == "-p":
        pcapdir = arg
    elif opt == "-c":
        dumpcpdu = open(arg, "a")
    elif opt == "-r":
        dumppcap = open(arg, "wb")
    elif opt == "-l":
        setloglevel(arg)
    else:
        assert False, "unhandled option"

""" Initialize output database """
con = lite.connect('sds.db')
cur = con.cursor()
create_schema(cur)

""" Handle signal """


def sigint(signal, frame):
    con.commit()
    sys.exit(0)


signal.signal(signal.SIGINT, sigint)

""" Queue to hold PDUs from tshark """
pduq = Queue()

""" Queue to hold packets from tetra-rx """
pcapq = Queue()

""" Spawn on thread for each tetra-rx """
if pcapdir:
    files = os.listdir(pcapdir)

    for f in files:
        ppath = pcapdir + "/" + f
        l("Adding packet input from %s" % ppath, "DBG")
        t = Thread(target=pcap_in_thr, args=(ppath, pcapq), name=f)
        t.daemon = True
        t.start()

""" Spawn tshark and its threads """
tshark_filter = subprocess.Popen([tshark_pipe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

t = Thread(target=tshark_in_thr, args=(tshark_filter, pcapq), name="tshark_in_thr")
t.daemon = True
t.start()

t = Thread(target=tshark_out_thr, args=(tshark_filter, pduq), name="tshark_out_thr")
t.daemon = True
t.start()

in_t = Thread(target=stdin_thr, args=(pduq,), name="stdin_thr")
in_t.daemon = True
in_t.start()

t = Thread(target=gc_thr, args=(multiframes, mlock), name="gc_thr")
t.daemon = True
t.start()

sqlite_wall = 0

""" Main loop. Get CPDUs from pduq and process them. """
while True:

    """ https://docs.python.org/2/library/sqlite3.html#multithreading
    We must do commit explicitly here, instead of a gc thread. Awww. """
    if time.time() - sqlite_wall > 10:
        try:
            con.commit()
        except:
            l("Cannot commit database", "WARN")
        sqlite_wall = time.time()

    try:
        line = pduq.get(timeout=1)
    except Empty:
        if not in_t.isAlive():
            con.commit()
            sys.exit(0)
        continue

    mlock.acquire()

    if len(line) < 2:
        mlock.release()
        continue

    pdata = line.split(";")

    if len(pdata) < 4:
        l("Skipping wrong input format line %s" % line, "WARN")
        mlock.release()
        continue

    payload = pdata[0].replace(":", "")
    arfcn = int(pdata[1])
    timeslot = int(pdata[2])
    frameno = int(pdata[3])

    key = (arfcn, timeslot)

    InMacType = getMacType(payload)
    fillbit = getStartFbi(payload)

    l("PDU: arfcn=%i, ts=%i, fn=%i, ct=%i, fill=%i, data=%s" % (arfcn, timeslot, frameno, InMacType, fillbit, payload),
      "DBG")

    if InMacType == Fragtype.MAC_SINGLE:
        # This is not a multiframe -> parse immediately
        parsesds(hex_to_binary(payload), arfcn, timeslot, 0, cur)

    if InMacType == Fragtype.MAC_START:
        # This is the first frame of a multiframe

        dkinit(arfcn, timeslot, multiframes)

        # This is the first frame. There should be nothing before it.
        if multiframes[key]:
            l("Lost multiframe on ARFCN %i TS %i" % (arfcn, timeslot), "INFO")
            for frm in multiframes[key]:
                s = pdu2string(frm)
                l("Lost: " + s, "DBG")
            multiframes[key] = []

        cpdu = CPDU(hex_to_binary(payload)[:-4], Fragtype.MAC_START, arfcn=arfcn, timeslot=timeslot)

        multiframes[key].append(cpdu)

    elif InMacType == Fragtype.MAC_INNER:
        # This is a frame of a multiframe, but neither the first, nor the last

        dkinit(arfcn, timeslot, multiframes)

        if not multiframes[key]:
            l("Stray MAC_INNER frame on ARFCN %i TS %i" % (arfcn, timeslot), "INFO")
            mlock.release()
            continue
        elif multiframes[(arfcn, timeslot)][0].ftype != Fragtype.MAC_START:
            l("%i stray MAC_INNER frames on ARFCN %i TS %i" % (len(multiframes[key]), arfcn, timeslot), "INFO")
            for frm in multiframes[key]:
                s = pdu2string(frm)
                l("Stray: " + s, "DBG")
            multiframes[key] = []
            mlock.release()
            continue

        tmsdu = ""
        if fillbit == 1:
            tmsdu = getFragTmsdu(stripFillingHex(payload))
        else:
            tmsdu = getFragTmsdu(hex_to_binary(payload))

        cpdu = CPDU(tmsdu, Fragtype.MAC_INNER, arfcn=arfcn, timeslot=timeslot)
        multiframes[key].append(cpdu)

    elif InMacType == Fragtype.MAC_END:
        # This is the last frame of a multiframe

        dkinit(arfcn, timeslot, multiframes)

        if not multiframes[key]:
            l("Stray MAC_END frame on ARFCN %i TS %i" % (arfcn, timeslot), "INFO")
            mlock.release()
            continue
        elif multiframes[(arfcn, timeslot)][0].ftype != Fragtype.MAC_START:
            l("BUG: %i stray frames in on ARFCN %i TS %i on MAC_END" % (len(multiframes[key]), arfcn, timeslot), "BUG")
            for frm in multiframes[key]:
                s = pdu2string(frm)
                l("Stray: " + s, "DBG")
            multiframes[key] = []
            mlock.release()
            continue

        tmsdu = ""
        if fillbit == 1:
            tmsdu = stripFillingBin(getEndTmsdu(hex_to_binary(payload)))
        else:
            tmsdu = getEndTmsdu(stripFillingBin(hex_to_binary(payload)))

        for frm in reversed(multiframes[key]):
            tmsdu = frm.data + tmsdu

        parsesds(tmsdu, arfcn, timeslot, 1, cur)
        del (multiframes[key])

    mlock.release()

log("Main thread died", "CRIT")
