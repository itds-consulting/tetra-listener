# TETRA Multiframe SDS decoder

This solution provides patches against [TETRA Listener](https://github.com/itds-consulting/tetra-listener) and scripts to correctly decode and assemble multi-frame SDS

## Architecture

  - Patched `tetra-rx` writes packets in PCAP format to FIFOs in set directory
  - `sds-parser.py` reads packets from FIFO pipes, combines them, feeds them through wireshark tetra dissector, combines them into multiframes and parses them
  - Output is given on both `stdout` and SQLite db file `sds.db`

## Dependencies

  - Install [TETRA Listener](https://github.com/itds-consulting/tetra-listener)
  - Have Python 2 and TShark available
  - Run this on Linux machine with /tmp available

## Installation

  - Apply patches
    - `cd tetra-listener ; git apply tetra-listener.patch`
    - `cd tetra-listener/osmo-tetra ; git apply osmo-tetra.patch`
  - Build `tetra-listener` again using `./build.sh`
  - Run `tetra-listener/radio-tetra/tetra.sh`
  - Run `sds-parser.py -p /tmp/fifos` and observe the output

## Troubleshooting

#### I'm not seeing any decoded SDS frames

Check if there are any GSMTAP frames on loopback interface (ie. `tshark -i lo`)

If there are not, check that

  - you are reading from the FIFO pipes (you have `sds-parser.py` running with correct arguments), otherwise tetra doesn't decode or send any data
  - you have correctly set `TUNE_PPM`, `TUNE_FREQ` variables in `radio-tetra/config.sh`

Try tuning your SDR using two steps:

  - execute `radio-tetra/tetra_cli_pwr.py` to get signal strengths on available channels, better signal strength is on top of the list
  - execute `radio-tetra/tetra_cli_auto_tune.py X`, where X is channel number from 0 to 71, from `radio-tetra/tetra_cli_pwr.py` output

#### In `tetra.sh` output I see number of "0" letters

This means your machine cannot correctly decode all the TETRA streams, try lowering `STREAMS` in `radio-tetra/config.sh`

## Tip

  - You can grep output of `sds-parser.py` for lines containing ASCII output, to search for text data
    - ie. `./sds-parser.py -p /tmp/fifos | grep "SDS T4 TRANSFER USER DATA TXT"`

## Example output

Running `sds-parser.py` correctly, you should see output similar to this (real data removed):

```
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
RAW> 
MAC_PDU_CHANNEL_ALLOCATION_FLAG:
MAC_PDU_TYPE:
MAC_FILL_BIT_INDICATION:
MAC_PDU_LENGTH:
MAC_PDU_ADDRESS:
TM-SDU LENGTH:
TM-SDU REAL LENGTH:
LLC_PDU_TYPE:
MLE_PROTOCOL_DISCRIMINATOR:
CMCE_PDU_TYPE:
DSDS_DATA_PDU_Calling_party_type_identifier:
DSDS_DATA_PDU_ADDRESS_SSI:
DSDS_DATA_PDU_ADDRESS_EXTENSION:
DSDS_DATA_PDU_SHORT_DATA_TYPE:
DSDS_DATA_USER_LENGTH_INDICATOR:
Debug: D-SDS-DATA RAW:
Debug: D-SDS-DATA RAW:
Debug: D-SDS-DATA BY LEN INDICATOR:
SDS_TYPE_4_PROTOCOL_INDENTIFIER:
SDS-TL MESAGE
SDS_TYPE_4_MESSAGE_TYPE:
SDS T4 TRANSFER DELIVERY REPORT REQUIRED:
SDS T4 TRANSFER SERVICE SELECTION / SHORT FROM REPORT:
SDS T4 TRANSFER STORAGE:
SDS T4 TRANSFER MESSAGE REFERENCE:
SDS T4 TRANSFER TEXT MESSAGE TIMESTAMP USED:
SDS T4 TRANSFER TEXT MESSAGE TEXT CODING SCHEME:
SDS T4 TRANSFER TEXT MESSAGE TIMESTAMP:
SDS T4 TRANSFER USER DATA ASCII INDEX: 
SDS T4 TRANSFER USER DATA LEN: 
SDS T4 TRANSFER USER DATA TXT: 
SDS T4 TRANSFER USER DATA HEX: 
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
```

Also you can get data from SQLite DB like this:

```
sqlite3 sds.db "select * from sds"
```
DB schema configuration is in `dbo.py`
