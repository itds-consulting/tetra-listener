#!/usr/bin/env python2.7
##################################################
# Gnuradio Python Flow Graph
# Title: Tetra Rx Multi
# Generated: Fri Oct 10 01:07:47 2014
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.filter import pfb
from optparse import OptionParser
import math
import osmosdr
import threading
import time

class tetra_rx_multi(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tetra Rx Multi")

        options = self.get_options()

        ##################################################
        # Variables
        ##################################################
        self.srate_rx = srate_rx = options.sample_rate
        self.channels = srate_rx / 25000
        self.srate_channel = 36000
        self.afc_period = 1
        self.afc_gain = 1.
        self.afc_channel = 28

        ##################################################
        # Rx Blocks and connections
        ##################################################
        self.rtlsdr_source = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.rtlsdr_source.set_sample_rate(srate_rx)
        self.rtlsdr_source.set_center_freq(options.frequency, 0)
        self.rtlsdr_source.set_freq_corr(options.ppm, 0)
        self.rtlsdr_source.set_dc_offset_mode(0, 0)
        self.rtlsdr_source.set_iq_balance_mode(0, 0)
        if options.gain is not None:
            self.rtlsdr_source.set_gain_mode(False, 0)
            self.rtlsdr_source.set_gain(36, 0)
        else:
            self.rtlsdr_source.set_gain_mode(True, 0)

        out_type, dst_path = options.output.split("://", 1)
        if out_type == "udp":
            dst_ip, dst_port = dst_path.split(':', 1)

        self.pfb_channelizer_ccf = pfb.channelizer_ccf(
              self.channels,
              (firdes.root_raised_cosine(1, srate_rx, 18000, 0.35, 1024)),
              36./25.,
              100)
        #self.pfb_channelizer_ccf.set_channel_map(([]))
        #self.pfb_channelizer_ccf.declare_sample_delay(0)

        self.digital_mpsk_receiver_cc = []
        self.blocks_sink = []
        for ch in range(0, self.channels):
            mpsk = digital.mpsk_receiver_cc(
                    4, math.pi/4, math.pi/100.0, -0.5, 0.5, 0.25, 0.001, 2, 0.001, 0.001)
            if out_type == 'udp':
                sink = blocks.udp_sink(gr.sizeof_gr_complex, dst_ip, int(dst_port)+ch, 1472, True)
            elif out_type == 'file':
                print dst_path % ch
                sink = blocks.file_sink(gr.sizeof_gr_complex*1, dst_path % ch, False)
                sink.set_unbuffered(True)
            else:
                raise ValueError("Invalid output URL '%s'" % options.output)

            self.connect((self.pfb_channelizer_ccf, ch),
                    (mpsk, 0),
                    (sink, 0))

            self.digital_mpsk_receiver_cc.append(mpsk)
            self.blocks_sink.append(sink)

        self.connect((self.rtlsdr_source, 0), (self.pfb_channelizer_ccf, 0))

        ##################################################
        # AFC blocks and connections
        ##################################################
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(self.srate_channel/(2*math.pi))
        samp_afc = self.srate_channel*self.afc_period
        self.blocks_moving_avg_ff_0 = blocks.moving_average_ff(samp_afc, 1./samp_afc)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((self.afc_gain, ))
        self.freq_err = blocks.probe_signal_f()

        self.connect((self.pfb_channelizer_ccf, self.afc_channel), (self.analog_quadrature_demod_cf_0, 0))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.blocks_moving_avg_ff_0, 0))
        self.connect((self.blocks_moving_avg_ff_0, 0), (self.freq_err, 0))

        def _afc_error_probe():
            while True:
                val = self.freq_err.level()
                print val
                time.sleep(self.afc_period)
        _afc_err_thread = threading.Thread(target=_afc_error_probe)
        _afc_err_thread.daemon = True
        _afc_err_thread.start()

    def get_srate_rx(self):
        return self.srate_rx

    def set_srate_rx(self, srate_rx):
        self.srate_rx = srate_rx
        self.rtlsdr_source.set_sample_rate(self.srate_rx)
        self.pfb_channelizer_ccf.set_taps((firdes.root_raised_cosine(1, self.srate_rx, 18000, 0.35, 1024)))

    def get_options(self):
        parser = OptionParser(option_class=eng_option)

        parser.add_option("-a", "--args", type="string", default="",
                help="gr-osmosdr device arguments")
        parser.add_option("-s", "--sample-rate", type="eng_float", default=1800000,
                help="set receiver sample rate (default 1800000, must be multiple of 900000)")
        parser.add_option("-f", "--frequency", type="eng_float", default=394.4e6,
                help="set receiver center frequency")
        parser.add_option("-p", "--ppm", type="eng_float", default=0.,
                help="Frequency correction as PPM")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                help="set receiver gain")
        parser.add_option("-o", "--output", type=str,
                help="output URL (eg file:///<FILE_PATH> or udp://DST_IP:PORT, use %d for channel no.")

        (options, args) = parser.parse_args()
        if len(args) != 0:
            parser.print_help()
            raise SystemExit, 1
        options.sample_rate = int(options.sample_rate)
        if options.sample_rate % 900000:
            parser.print_help()
            raise SystemExit, 1
        return (options)


if __name__ == '__main__':
    tb = tetra_rx_multi()
    tb.start()
    tb.wait()
