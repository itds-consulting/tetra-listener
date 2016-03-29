from libdeka import Struct

import time
from datetime import datetime

"""The structure to hold one MAC fragment."""
CPDU_t = Struct("CPDU", "time " +  # UNIX timestamp this has been first seen
                "ftype " +  # fragment type
                "arfcn " +
                "timeslot " +
                "data"  # fragment payload
                )


def CPDU(data, ftype, stime=time.time(), arfcn=0, timeslot=0):
    return CPDU_t(stime, ftype, arfcn, timeslot, data)


def pdu2string(pdu):
    """ Return string with pretty-printed CPDU """

    s = ""
    s += datetime.fromtimestamp(pdu.time).strftime('%Y-%m-%d %H:%M:%S ')
    s += pdu.data

    return s
