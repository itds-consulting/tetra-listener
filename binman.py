import binascii


def byte_to_binary(n):
    """ 5 -> "00000101" """
    return ''.join(str((n & (1 << i)) and 1) for i in reversed(range(8)))


def hex_to_binary(h):
    """" "1f" -> "00011111" """
    return ''.join(byte_to_binary(ord(b)) for b in binascii.unhexlify(h))


def ascidxFromBites(in_stream):
    str_len = len(in_stream) // 8
    asc_idx = 0
    for x in xrange(0, str_len):
        bytetmp = int(in_stream[x * 8:(x * 8) + 8], 2)
        if 31 < bytetmp < 127:  # and bytetmp != 44 and bytetmp != 96 and bytetmp != 39 and bytetmp != 92:
            asc_idx += 1
    if str_len > 0:
        return (asc_idx * 100) // str_len
    else:
        return 0


def strFromBites(in_stream):
    """ "01001001010101000100010001010011" -> "ITDS" """
    outasc = ""
    for x in xrange(0, len(in_stream) // 8):
        bytetmp = int(in_stream[x * 8:(x * 8) + 8], 2)
        if 31 < bytetmp < 127:  # and bytetmp != 44 and bytetmp != 96 and bytetmp != 39 and bytetmp != 92:
            outasc += chr(bytetmp)
        else:
            outasc += " "
    return outasc


def hexFromBites(in_stream):
    """ "01001001010101000100010001010011" -> "49:54:44:53:" """
    outhex = ""
    for x in xrange(0, len(in_stream) // 8):
        bytetmp = int(in_stream[x * 8:(x * 8) + 8], 2)
        outhex = outhex + format(bytetmp, '02X') + ":"
    return outhex

def bitesFromHex(in_hex):
    """ "0A:FF:10:AA:12" -> "0000101011111111000100001010101000010010" """
    outbin = ""
    if in_hex[0] == ":":
        in_hex = in_hex[1:]

    if ':' in in_hex:
        outbin = ''.join([hex_to_binary(x) for x in in_hex.split(':')])
    else:
        outbin = ''.join([hex_to_binary(in_hex[i*2:i*2+2]) for i in range(len(in_hex) // 2)])

    return outbin
