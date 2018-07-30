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

### `tshark died` appears when running `sds-parser.py`

Probable cause is that tshark doesn't support used filter params.
Try editing file `config.py`, disabling the default `tshark_pipe` variable, and enabling the other one (which has _element suffixes to filter element names) 

## Tip

  - You can grep output of `sds-parser.py` for lines containing ASCII output, to search for text data
    - ie. `./sds-parser.py -p /tmp/fifos | grep "SDS T4 TRANSFER USER DATA TXT"`

## Example output

Running `sds-parser.py` correctly, you should see output similar to this (real data removed):

```
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
RAW> 20:C9:00:00:65:04:9E:FF:FF:F0:61:02:08:00:80:05:05:A1:BD:AB:20:28:20:00:28:00:10:80:00:00:00:00:00:00:
MAC_PDU_CHANNEL_ALLOCATION_FLAG: 0
MAC_PDU_TYPE: 0
MAC_FILL_BIT_INDICATION: 1
MAC_PDU_LENGTH: 25
MAC_PDU_ADDRESS: 101 (TO)
TM-SDU LENGTH: 157 bits
DSDS_DATA_USER_LENGTH_INDICATOR: 64
Debug: D-SDS-DATA RAW:     Ahoj    
Debug: D-SDS-DATA RAW: 82:00:20:01:41:68:6F:6A:C8:0A:08:00:
Debug: D-SDS-DATA BY LEN INDICATOR:     Ahoj
SDS_TYPE_4_PROTOCOL_INDENTIFIER: 130
SDS-TL MESAGE
SDS_TYPE_4_MESSAGE_TYPE: 0
SDS T4 TRANSFER DELIVERY REPORT REQUIRED: 0
SDS T4 TRANSFER SERVICE SELECTION / SHORT FROM REPORT: 0
SDS T4 TRANSFER STORAGE: 0
SDS T4 TRANSFER MESSAGE REFERENCE: 32
SDS T4 TRANSFER TEXT MESSAGE TIMESTAMP USED: 0
SDS T4 TRANSFER TEXT MESSAGE TEXT CODING SCHEME: 1
SDS T4 TRANSFER TEXT MESSAGE TIMESTAMP: None
SDS T4 TRANSFER USER DATA ASCII INDEX: 100
SDS T4 TRANSFER USER DATA LEN: 32
SDS T4 TRANSFER USER DATA TXT: Ahoj
SDS T4 TRANSFER USER DATA HEX: 41:68:6F:6A:
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
```

Also you can get data from SQLite DB like this:

```
sqlite3 sds.db "select * from sds"
```
DB schema configuration is in `dbo.py`
