# Command into which PCAP data from the network are piped.
tshark_pipe = "tshark -l -i - -E separator=\";\" -Y 'tetra.MAC_END_DOWNLINK or tetra.MAC_FRAG or tetra.d_SDS_Data' -T fields -e tetra.pdu -e gsmtap.arfcn -e gsmtap.ts -e frame.number 2>/dev/null"
# alternative, comment out previous and un-comment this one, if you see `tshark died` when running `sds-parser.py`
#tshark_pipe = "tshark -l -i - -E separator=\";\" -Y 'tetra.MAC_END_DOWNLINK_element or tetra.MAC_FRAG_element or tetra.d_SDS_Data_element' -T fields -e tetra.pdu -e gsmtap.arfcn -e gsmtap.ts -e frame.number 2>/dev/null"

# Amount of seconds after which the garbage collector should remove unfinished multiframes.
multiframe_tx_interval = 10
