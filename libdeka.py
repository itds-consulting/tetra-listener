from __future__ import print_function
import time
from datetime import datetime
from threading import Lock


# class generator like namedtuple, but not immutable
# https://stackoverflow.com/questions/3648442/python-how-to-define-a-structure-like-in-c/3648450#3648450
def Struct(name, fields):
    fields = fields.split()

    def init(self, *values):
        for field, value in zip(fields, values):
            self.__dict__[field] = value

    cls = type(name, (object,), {'__init__': init})
    return cls


class bcolors:
    def __init__(self):
        pass

    PURPLE = '\033[95m'
    BLUE = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


loglevel = -1
loglevels = ["DBG", "SDS", "INFO", "WARN", "CRIT"]


def setloglevel(l):
    global loglevel
    loglevel = loglevels.index(l)


loglock = Lock()


def mylog(s, l="INFO"):
    """ Logging function. Params: message, loglevel."""

    if loglevels.index(l) < loglevel:
        return

    loglock.acquire()

    if l == "DBG":
        print(bcolors.PURPLE, end="")
    elif l == "INFO":
        print(bcolors.BLUE, end="")
    elif l == "WARN":
        print(bcolors.YELLOW, end="")
    elif l == "CRIT":
        print(bcolors.RED, end="")
    elif l == "SDS":
        print(bcolors.GREEN, end="")

    if l != "SDS":
        print(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S '), end="")

    print(s)

    print(bcolors.ENDC, end="")

    loglock.release()
