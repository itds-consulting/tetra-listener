#!/usr/bin/env python2.7
##################################################
# Gnuradio Python Flow Graph
# Title: Tetra Rx Multi
# Generated: Fri Oct 10 01:07:47 2014
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import digital;import cmath
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.filter import pfb
from optparse import OptionParser
import osmosdr

class tetra_rx_multi(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tetra Rx Multi")

        ##################################################
        # Variables
        ##################################################
        self.srate_rx = srate_rx = 1800000
        self.channels = 36*2

        ##################################################
        # Blocks
        ##################################################
        self.rtlsdr_source = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.rtlsdr_source.set_sample_rate(srate_rx)
        self.rtlsdr_source.set_center_freq(424e6, 0)
        self.rtlsdr_source.set_freq_corr(36, 0)
        self.rtlsdr_source.set_dc_offset_mode(0, 0)
        self.rtlsdr_source.set_iq_balance_mode(0, 0)
        self.rtlsdr_source.set_gain_mode(False, 0)
        self.rtlsdr_source.set_gain(36, 0)

        self.pfb_channelizer_ccf = pfb.channelizer_ccf(
        	  self.channels,
        	  (firdes.root_raised_cosine(1, srate_rx, 18000, 0.35, 1024)),
        	  36./25.,
        	  100)
        #self.pfb_channelizer_ccf.set_channel_map(([]))
        #self.pfb_channelizer_ccf.declare_sample_delay(0)

        self.analog_feedforward_agc_cc = []
        self.digital_mpsk_receiver_cc = []
        self.blocks_sink = []
        for ch in range(0, self.channels):
            #agc = analog.feedforward_agc_cc(1024, 1.0)
            if ch % 2:
                mpsk = blocks.copy(8)
                sink = blocks.null_sink(8)
            else:
                mpsk = digital.mpsk_receiver_cc(4, cmath.pi/4, cmath.pi/100.0, -0.5, 0.5, 0.25, 0.001, 2, 0.001, 0.001)
                sink = blocks.udp_sink(gr.sizeof_float*2, "", 60001, 1472, True)
                #sink = blocks.null_sink(8)
            self.connect((self.pfb_channelizer_ccf, ch),
                    #(agc, 0),
                    (mpsk, 0),
                    (sink, 0))

            #self.analog_feedforward_agc_cc.append(agc)
            #self.digital_mpsk_receiver_cc.append(mpsk)
            self.blocks_sink.append(sink)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.rtlsdr_source, 0), (self.pfb_channelizer_ccf, 0))


    def get_srate_rx(self):
        return self.srate_rx

    def set_srate_rx(self, srate_rx):
        self.srate_rx = srate_rx
        self.rtlsdr_source.set_sample_rate(self.srate_rx)
        self.pfb_channelizer_ccf.set_taps((firdes.root_raised_cosine(1, self.srate_rx, 18000, 0.35, 1024)))

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = tetra_rx_multi()
    tb.start()
    tb.wait()
