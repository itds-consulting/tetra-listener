#!/usr/bin/env python2.7

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.filter import freq_xlating_fft_filter_ccc
from gnuradio.filter import pfb
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import SimpleXMLRPCServer
import math
import osmosdr
import threading
import time
import os

##################################################
# Example: Using FCL to receive the Tetra network.
# 
# With this, I was able to receive 20 channels in parallel on a Radxa Rock Pro
#  (hardware similar to Raspberry Pi 2). I used
# https://brmlab.cz/project/sdr/tetra and
# https://github.com/itds-consulting/tetra-multiframe-sds
# 
# mkfifo /tmp/myout.ch; mkfifo /tmp/pipe
#
# The exact commandline used was:
# rtl_sdr -f 424150e3 -s 1.8e6 -g 25 -p 15 - | ./fcl -n 72 -s 50 -f "./fir.py 1.8e6 18.5e3 1151 rcos" -c 23,13,40,69,59,7,42,54,5,14,4,56,45,46,67,55,66,44,71,49 -t 1 -i U8 -r /tmp/pipe -o /tmp/myout.ch
# 
# TODO: Tuning error is printed to stdout, but not used.
# you have to manually echo 1/-1 to /tmp/pipe to adjust the frequency.
# 
##################################################


class tetra_rx_multi(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Tetra Rx Multi")

        options = self.get_options()

        self.src = blocks.file_source(gr.sizeof_gr_complex*1, "/tmp/myout2.ch", False)

        ##################################################
        # Variables
        ##################################################
        self.srate_rx = srate_rx = options.sample_rate
        self.channels = srate_rx / 25000
        self.srate_channel = 36000
        self.afc_period = 15
        self.afc_gain = 0.01
        self.afc_channel = options.auto_tune or -1
        self.afc_ppm_step = 100
        self.debug = options.debug
        self.last_pwr = -100000
        self.sig_det_period = 10
        self.sig_det_bw = sig_det_bw = options.sig_detection_bw or srate_rx
        if self.sig_det_bw <= 1.:
            self.sig_det_bw *= srate_rx
        self.sig_det_threshold = options.sig_detection_threshold
        self.sig_det_channels = []
        for ch in range(self.channels):
            if ch >= self.channels / 2:
                ch_ = (self.channels - ch - 1)
            else:
                ch_ = ch
            if (float(ch_) / self.channels * 2) <= (self.sig_det_bw / srate_rx):
                self.sig_det_channels.append(ch)

        self.channels = 20

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

        out_type, dst_path = options.output.split("://", 1)
        if out_type == "udp":
            dst_ip, dst_port = dst_path.split(':', 1)

        self.blocks_deinterleave_0 = blocks.deinterleave(gr.sizeof_gr_complex*1, 1)

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
            mpsk = digital.mpsk_receiver_cc(
                    4, math.pi/4, math.pi/100.0, -0.5, 0.5, 0.25, 0.001, 2, 0.001, 0.001)
            diff_phasor = digital.diff_phasor_cc()
            complex_to_arg = blocks.complex_to_arg(1)
            multiply_const = blocks.multiply_const_vff((2./math.pi, ))
            add_const = blocks.add_const_vff((1.5, ))
            float_to_uchar = blocks.float_to_uchar()
            map_bits = digital.map_bb(([3, 2, 0, 1, 3]))
            unpack_k_bits = blocks.unpack_k_bits_bb(2)

            brmchannels = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71]
            #brmchannels = [11,4,3,64,45,47,53,8,68,6,56,49,17,54,65,5,71,22,48,7,50] # itds kancl
            #brmchannels = [23,13,40,69,59,7,42,54,5,14,4,56,45,46,67,55,66,44,71,49,31,57,0,65,70] # doma - dole
            #brmchannels = [23,13,59,40,69,7,49,60,42,70,4,50,66,67,3,14,57,33,46,22,68,32,39,24,6,12,43,58,48,17,5,56,65,29,54,30,16,52,53,41,47,2,34,44,8] # doma - strecha
            #brmchannels = [67, 7, 23, 70] # doma - strecha - SDS
            #brmchannels = [67, 7, 23, 70,9,71,64,63,62,61,55,51,45,38,37,36,35,31,28,27,26,25,21,20,19,18,15,11,10,1,0] # doma - strecha - komplement


            if out_type == 'udp':
                sink = blocks.udp_sink(gr.sizeof_gr_char, dst_ip, int(dst_port)+ch, 1472, True)
            elif out_type == 'file':
                sink = blocks.file_sink(gr.sizeof_char, dst_path % (ch+30), False)
                sink.set_unbuffered(True)
            else:
                raise ValueError("Invalid output URL '%s'" % options.output)

            print "connect %i"%ch

            if ch in brmchannels:
                self.connect((self.blocks_deinterleave_0, ch),
                    #(squelch, 0),
                    (mpsk, 0),
                    (diff_phasor, 0),
                    (complex_to_arg, 0),
                    (multiply_const, 0),
                    (add_const, 0),
                    (float_to_uchar, 0),
                    (map_bits, 0),
                    (unpack_k_bits, 0),
                    (sink, 0))


            self.digital_mpsk_receiver_cc.append(mpsk)
            self.diff_phasor.append(diff_phasor)
            self.complex_to_arg.append(complex_to_arg)
            self.multiply_const.append(multiply_const)
            self.add_const.append(add_const)
            self.float_to_uchar.append(float_to_uchar)
            self.map_bits.append(map_bits)
            self.unpack_k_bits.append(unpack_k_bits)
            self.blocks_sink.append(sink)

        self.connect(
                (self.src, 0),
                (self.blocks_deinterleave_0, 0))

        ##################################################
        # signal strenght identification
        ##################################################
        '''
        self.pwr_probes = []
        for ch in range(self.channels):
            pwr_probe = analog.probe_avg_mag_sqrd_c(0, 1./self.srate_channel)
            self.pwr_probes.append(pwr_probe)
            print "connect %i"%ch
            self.connect((self.blocks_deinterleave_0, ch), (pwr_probe, 0))
        def _sig_det_probe():
            while True:
                pwr = [self.pwr_probes[ch].level()
                        for ch in range(self.channels)
                        if ch in self.sig_det_channels]
                pwr = [10 * math.log10(p) for p in pwr if p > 0.]
                if not pwr:
                    continue
                pwr = min(pwr) + self.sig_det_threshold
                print "power threshold target %f"%pwr
                if abs(pwr - self.last_pwr) > (self.sig_det_threshold / 2):
                    for s in []:
                        s.set_threshold(pwr)
                    self.last_pwr = pwr
                time.sleep(self.sig_det_period)

        if self.sig_det_threshold is not None:
            self._sig_det_probe_thread = threading.Thread(target=_sig_det_probe)
            self._sig_det_probe_thread.daemon = True
            self._sig_det_probe_thread.start()
        '''
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

        def _afc_probe():
            rt = 0.0
            while True:
                time.sleep(self.afc_period)
                if self.afc_channel == -1:
                    continue
                err = self.afc_probe.level()
                freq = err * self.afc_gain
                print "err: %f\tfreq: %f\trt %f" % (err, freq, rt)
                changed = False
                if err < -1:
                    rt += 0.1
                    changed = True
                elif err > 1:
                    rt -= 0.1
                    changed = True

                if changed:
                    os.system("echo \"setrot %f\" | nc localhost 3334"%rt)


        self.afc_channel = 0
        self._afc_err_thread = threading.Thread(target=_afc_probe)
        self._afc_err_thread.daemon = True
        self._afc_err_thread.start()

        for ch in range(self.channels):
            print "connect %i"%ch
            self.connect((self.blocks_deinterleave_0, ch), (self.afc_selector, ch))
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
        return

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
                help="Band width used for detection of noise level, values <= 1. are interpreted as a fraction of sample rate.")
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
    print "ahoj"
    tb = tetra_rx_multi()
    tb.start()
    tb.wait()
