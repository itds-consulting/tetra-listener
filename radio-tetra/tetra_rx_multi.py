#!/usr/bin/env python2.7

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.filter import pfb
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import SimpleXMLRPCServer
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
        self.afc_period = 5
        self.afc_gain = 1.
        self.afc_channel = options.auto_tune or -1
        self.afc_ppm_step = options.frequency / 1.e6
        self.debug = options.debug
        self.last_pwr = -100000
        self.sig_det_period = 1
        self.sig_det_bw = sig_det_bw = options.sig_detection_bw or srate_rx
        self.sig_det_threshold = options.sig_detection_threshold
        self.sig_det_channels = []
        for ch in range(self.channels):
            if ch >= self.channels / 2:
                ch_ = (self.channels - ch - 1)
            else:
                ch_ = ch
            if (float(ch_) / self.channels * 2) <= (self.sig_det_bw / srate_rx):
                self.sig_det_channels.append(ch)

        ##################################################
        # RPC server
        ##################################################
        self.xmlrpc_server = SimpleXMLRPCServer.SimpleXMLRPCServer(
                ("localhost", options.listen_port), allow_none=True)
        self.xmlrpc_server.register_instance(self)
        threading.Thread(target=self.xmlrpc_server.serve_forever).start()

        ##################################################
        # Rx Blocks and connections
        ##################################################
        self.src = osmosdr.source( args=options.args )
        self.src.set_sample_rate(srate_rx)
        self.src.set_center_freq(options.frequency, 0)
        self.src.set_freq_corr(options.ppm, 0)
        self.src.set_dc_offset_mode(0, 0)
        self.src.set_iq_balance_mode(0, 0)
        if options.gain is not None:
            self.src.set_gain_mode(False, 0)
            self.src.set_gain(36, 0)
        else:
            self.src.set_gain_mode(True, 0)

        out_type, dst_path = options.output.split("://", 1)
        if out_type == "udp":
            dst_ip, dst_port = dst_path.split(':', 1)

        self.channelizer = pfb.channelizer_ccf(
              self.channels,
              (firdes.root_raised_cosine(1, srate_rx, 18000, 0.35, 1024)),
              36./25.,
              100)

        self.squelch = []
        self.digital_mpsk_receiver_cc = []
        self.diff_phasor = []
        self.complex_to_arg = []
        self.multiply_const = []
        self.add_const = []
        self.float_to_uchar = []
        self.map_bits = []
        self.unpack_k_bits = []
        self.blocks_sink = []
        for ch in range(0, self.channels):
            squelch = analog.pwr_squelch_cc(0, 0.001, 0, True)
            mpsk = digital.mpsk_receiver_cc(
                    4, math.pi/4, math.pi/100.0, -0.5, 0.5, 0.25, 0.001, 2, 0.001, 0.001)
            diff_phasor = digital.diff_phasor_cc()
            complex_to_arg = blocks.complex_to_arg(1)
            multiply_const = blocks.multiply_const_vff((2./math.pi, ))
            add_const = blocks.add_const_vff((1.5, ))
            float_to_uchar = blocks.float_to_uchar()
            map_bits = digital.map_bb(([3, 2, 0, 1, 3]))
            unpack_k_bits = blocks.unpack_k_bits_bb(2)

            if out_type == 'udp':
                sink = blocks.udp_sink(gr.sizeof_gr_char, dst_ip, int(dst_port)+ch, 1472, True)
            elif out_type == 'file':
                sink = blocks.file_sink(gr.sizeof_char, dst_path % ch, False)
                sink.set_unbuffered(True)
            else:
                raise ValueError("Invalid output URL '%s'" % options.output)

            self.connect((self.channelizer, ch),
                    (squelch, 0),
                    (mpsk, 0),
                    (diff_phasor, 0),
                    (complex_to_arg, 0),
                    (multiply_const, 0),
                    (add_const, 0),
                    (float_to_uchar, 0),
                    (map_bits, 0),
                    (unpack_k_bits, 0),
                    (sink, 0))

            self.squelch.append(squelch)
            self.digital_mpsk_receiver_cc.append(mpsk)
            self.diff_phasor.append(diff_phasor)
            self.complex_to_arg.append(complex_to_arg)
            self.multiply_const.append(multiply_const)
            self.add_const.append(add_const)
            self.float_to_uchar.append(float_to_uchar)
            self.map_bits.append(map_bits)
            self.unpack_k_bits.append(unpack_k_bits)
            self.blocks_sink.append(sink)

        self.connect((self.src, 0), (self.channelizer, 0))

        ##################################################
        # signal strenght identification
        ##################################################
        self.pwr_probes = []
        for ch in range(self.channels):
            pwr_probe = analog.probe_avg_mag_sqrd_c(0, 1./self.srate_channel)
            self.pwr_probes.append(pwr_probe)
            self.connect((self.channelizer, ch), (pwr_probe, 0))
        def _sig_det_probe():
            while True:
                pwr = [self.pwr_probes[ch].level()
                        for ch in range(self.channels)
                        if ch in self.sig_det_channels]
                pwr = [10 * math.log10(p) for p in pwr if p > 0.]
                if not pwr:
                    continue
                pwr = min(pwr) + self.sig_det_threshold
                if abs(pwr - self.last_pwr) > (self.sig_det_threshold / 2):
                    for s in self.squelch:
                        s.set_threshold(pwr)
                    self.last_pwr = pwr
                time.sleep(self.sig_det_period)

        if self.sig_det_threshold is not None:
            self._sig_det_probe_thread = threading.Thread(target=_sig_det_probe)
            self._sig_det_probe_thread.daemon = True
            self._sig_det_probe_thread.start()

        ##################################################
        # AFC blocks and connections
        ##################################################
        self.afc_selector = grc_blks2.selector(
                item_size=gr.sizeof_gr_complex,
                num_inputs=self.channels,
                num_outputs=1,
                input_index=0,
                output_index=0,
                )

        self.afc_demod = analog.quadrature_demod_cf(self.srate_channel/(2*math.pi))
        samp_afc = self.srate_channel*self.afc_period / 2
        self.afc_avg = blocks.moving_average_ff(samp_afc, 1./samp_afc*self.afc_gain)
        self.afc_probe = blocks.probe_signal_f()

        def _afc_error_probe():
            while True:
                time.sleep(self.afc_period)
                if self.afc_channel == -1:
                    continue
                err = self.afc_probe.level()
                if err > self.afc_ppm_step:
                    d = -1
                elif err < -self.afc_ppm_step:
                    d = 1
                else:
                    continue
                ppm = self.src.get_freq_corr() + d
                if self.debug:
                    print "PPM: % 4d err: %f" % (ppm, err, )
                self.src.set_freq_corr(ppm)
        self._afc_err_thread = threading.Thread(target=_afc_error_probe)
        self._afc_err_thread.daemon = True
        self._afc_err_thread.start()

        for ch in range(self.channels):
            self.connect((self.channelizer, ch), (self.afc_selector, ch))
        self.connect(
                (self.afc_selector, 0),
                (self.afc_demod, 0),
                (self.afc_avg, 0),
                (self.afc_probe, 0))

        if self.afc_channel != -1:
            self.afc_selector.set_input_index(self.afc_channel)

    def get_srate_rx(self):
        return self.srate_rx

    def set_srate_rx(self, srate_rx):
        self.srate_rx = srate_rx
        self.src.set_sample_rate(self.srate_rx)
        self.channelizer.set_taps((firdes.root_raised_cosine(1, self.srate_rx, 18000, 0.35, 1024)))

    def get_channels_pwr(self, channels=None):
        if channels is None:
            channels = range(len(self.pwr_probes))
        pwr = []
        for ch in channels:
            p = self.pwr_probes[ch].level()
            if p > 0.:
                p = 10 * math.log10(p)
            else:
                p = None
            pwr.append((p, ch, ))
        return pwr

    def get_auto_tune(self):
        return self.afc_channel

    def set_auto_tune(self, afc_channel):
        self.afc_channel = afc_channel
        if afc_channel != -1:
            self.afc_selector.set_input_index(afc_channel)

    def get_options(self):
        parser = OptionParser(option_class=eng_option)

        parser.add_option("-a", "--args", type="string", default="",
                help="gr-osmosdr device arguments")
        parser.add_option("-d", "--debug", action="store_true", default=False,
                help="Print out debug informations")
        parser.add_option("-f", "--frequency", type="eng_float", default=394.4e6,
                help="set receiver center frequency")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                help="set receiver gain")
        parser.add_option("-p", "--ppm", type="eng_float", default=0.,
                help="Frequency correction as PPM")
        parser.add_option("-o", "--output", type=str,
                help="output URL (eg file:///<FILE_PATH> or udp://DST_IP:PORT, use %d for channel no.")
        parser.add_option("-s", "--sample-rate", type="eng_float", default=1800000,
                help="set receiver sample rate (default 1800000, must be multiple of 900000)")
        parser.add_option("-t", "--auto-tune", type=int, default=None,
                help="Enable automatic PPM corection based on channel N")
        parser.add_option("--sig-detection-bw", type="eng_float", default=None,
                help="Band width used for detection of noise level")
        parser.add_option("--sig-detection-threshold", type="eng_float", default=6,
                help="Signal strenght (above noise) when channel decoding starts")
        parser.add_option("-l", "--listen-port", type=int, default=60200,
                help="Listen port for XML-RPC server")

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
