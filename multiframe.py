#!/usr/bin/python

from binman import *
from fragtype import Fragtype


def getMacType(in_pdu):
    """ Return multiframeness of a PDU (see Fragtype class) """

    bitstream = hex_to_binary(in_pdu)

    macpdutype = int(bitstream[:2], 2)

    if macpdutype == 0:
        subidx = 7
        macpdulen = int(bitstream[subidx:subidx + 6], 2)

        if macpdulen == 63:
            return Fragtype.MAC_START
        else:
            return Fragtype.MAC_SINGLE

    elif macpdutype == 1:
        subidx = 2
        macpdusubtype = int(bitstream[subidx:subidx + 1], 2)

        if macpdusubtype == 0:
            return Fragtype.MAC_INNER
        elif macpdusubtype == 1:
            return Fragtype.MAC_END


def getStartFbi(in_pdu):
    bitstream = hex_to_binary(in_pdu)
    return int(bitstream[2:3], 2)


def getFrEndFbi(in_pdu):
    bitstream = hex_to_binary(in_pdu)
    return int(bitstream[3:4], 2)


def stripFillingBin(in_bitstream):
    bitstream = in_bitstream
    for x in xrange(0, len(bitstream)):
        streamidx = len(bitstream) - 1 - x
        if int(bitstream[streamidx:streamidx + 1], 2) == 1:
            return bitstream[:len(bitstream) - x - 1]


def stripFillingHex(in_pdu):
    bitstream = hex_to_binary(in_pdu)
    for x in xrange(0, len(bitstream)):
        streamidx = len(bitstream) - 1 - x
        if int(bitstream[streamidx:streamidx + 1], 2) == 1:
            return bitstream[:len(bitstream) - x - 1]


def getFragTmsdu(in_bitstream):
    if len(in_bitstream) == 272:
        return in_bitstream[4:-4]
    return in_bitstream[4:]


def getEndTmsdu(in_bitstream):
    offset = 11

    mac_end_li = int(in_bitstream[5:5 + 6], 2)

    if int(in_bitstream[offset:offset + 1], 2) == 1:
        offset = offset + 1 + 8
    else:
        offset += 1

    if int(in_bitstream[offset:offset + 1], 2) == 1:
        offset = offset + 1 + 22

        if int(in_bitstream[offset:offset + 1], 2) == 1:
            offset = offset + 1 + 10
        else:
            offset += 1
    else:
        offset += 1

    # if int(in_bitstream[offset:offset+2],2) == 0:
    #  offset = offset + 4
    # else:
    #  offset = offset + 2

    outtmsdu = in_bitstream[offset:offset + (mac_end_li * 8)]

    # print "END_MAC_LEN: " + str(mac_end_li*8)
    # print "END_MAC_LEN_STRIPED: " + str(len(outtmsdu))

    return outtmsdu
