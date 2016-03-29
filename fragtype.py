class Fragtype:
    """ Type of fragment of multiframe """

    # One PDU contains the entire frame
    def __init__(self):
        pass

    MAC_SINGLE = 0

    # Leading frame of a multiframe
    MAC_START = 1
    # Stuffing frame of a multiframe
    MAC_INNER = 2
    # Last frame of a multiframe
    MAC_END = 3
