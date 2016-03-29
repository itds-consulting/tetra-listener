import struct

'''PCAP file header.
https://wiki.wireshark.org/Development/LibpcapFileFormat#Global_Header '''
pcap_header = struct.pack("@IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
