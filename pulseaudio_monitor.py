import sys
from Queue import Queue
from ctypes import POINTER, c_ubyte, c_void_p, c_ulong, cast
import random

# From https://github.com/Valodim/python-pulseaudio
from pulseaudio.lib_pulseaudio import *

# edit to match your sink
SINK_NAME = 'alsa_output.pci-0000_00_1b.0.analog-stereo'
METER_RATE = 256
MAX_SAMPLE_VALUE = 127
DISPLAY_SCALE = 100
MAX_SPACES = MAX_SAMPLE_VALUE >> DISPLAY_SCALE

colors=['red','orange','yellow','green','sky','blue','purple','white']
intensity=['left','middle','right']


class PeakMonitor(object):

    def __init__(self, sink_name, rate):
        self.sink_name = sink_name
        self.rate = rate

        # Wrap callback methods in appropriate ctypefunc instances so
        # that the Pulseaudio C API can call them
        self._context_notify_cb = pa_context_notify_cb_t(self.context_notify_cb)
        self._sink_info_cb = pa_sink_info_cb_t(self.sink_info_cb)
        self._stream_read_cb = pa_stream_request_cb_t(self.stream_read_cb)

        # stream_read_cb() puts peak samples into this Queue instance
        self._samples = Queue()

        # Create the mainloop thread and set our context_notify_cb
        # method to be called when there's updates relating to the
        # connection to Pulseaudio
        _mainloop = pa_threaded_mainloop_new()
        _mainloop_api = pa_threaded_mainloop_get_api(_mainloop)
        context = pa_context_new(_mainloop_api, 'peak_demo')
        pa_context_set_state_callback(context, self._context_notify_cb, None)
        pa_context_connect(context, None, 0, None)
        pa_threaded_mainloop_start(_mainloop)

    def __iter__(self):
        while True:
            yield self._samples.get()

    def context_notify_cb(self, context, _):
        state = pa_context_get_state(context)

        if state == PA_CONTEXT_READY:
            print "Pulseaudio connection ready..."
            # Connected to Pulseaudio. Now request that sink_info_cb
            # be called with information about the available sinks.
            o = pa_context_get_sink_info_list(context, self._sink_info_cb, None)
            pa_operation_unref(o)

        elif state == PA_CONTEXT_FAILED :
            print "Connection failed"

        elif state == PA_CONTEXT_TERMINATED:
            print "Connection terminated"

    def sink_info_cb(self, context, sink_info_p, _, __):
        if not sink_info_p:
            return

        sink_info = sink_info_p.contents
        print '-'* 60
        print 'index:', sink_info.index
        print 'name:', sink_info.name
        print 'description:', sink_info.description

        if sink_info.name == self.sink_name:
            # Found the sink we want to monitor for peak levels.
            # Tell PA to call stream_read_cb with peak samples.
            print
            print 'setting up peak recording using', sink_info.monitor_source_name
            print
            samplespec = pa_sample_spec()
            samplespec.channels = 1
            samplespec.format = PA_SAMPLE_U8
            samplespec.rate = self.rate

            pa_stream = pa_stream_new(context, "peak detect demo", samplespec, None)
            pa_stream_set_read_callback(pa_stream,
                                        self._stream_read_cb,
                                        sink_info.index)
            pa_stream_connect_record(pa_stream,
                                     sink_info.monitor_source_name,
                                     None,
                                     PA_STREAM_PEAK_DETECT)

    def stream_read_cb(self, stream, length, index_incr):
        data = c_void_p()
        pa_stream_peek(stream, data, c_ulong(length))
        data = cast(data, POINTER(c_ubyte))
        for i in xrange(length):
            self._samples.put(data[i] - 128) ##Range is 128-256.
        pa_stream_drop(stream)

def main():
	monitor = PeakMonitor(SINK_NAME, METER_RATE)
	thres_min= 15				# Minimun threshold.
	thres= thres_min			# The threshold.
	thres_max= thres_min		# Max peak vlue.
	thres_dec_count= 0			# Sample meter to detect volume drop down.
	
	param_peak_reactivity= 5 	# Threshold under peak. Highers values means higher reactivity to peak vibratos and near peak reverbs.
	param_decr_count_thres= 300	# Number of continued sub-threshold samples to detect volume drop.
	param_decr_value= 0.1		# Highers values decrease the threshold faster whean param_thres_count is not reached, i.e pendient after peak, before drop.
	param_decr_value_on_drop= 5	# Highers values decrease the threshold faster whean param_thres_count has reached, i.e pendient after drop.

	for sample in monitor:
		if sample>thres:
			print random.choice(colors),';',random.choice(colors),';',random.choice(colors)
			sys.stdout.flush()
			thres_dec_count=0
			if sample > thres_max:
				thres_max = sample;
				thres = thres_max-param_peak_reactivity
		else:
			thres_dec_count = thres_dec_count+1
			if thres_dec_count >= param_decr_count_thres:
				thres_max=thres_max-param_decr_value_on_drop
				thres=thres-param_decr_value_on_drop
			else:
				thres_max=thres_max-param_decr_value
				thres=thres-param_decr_value
		if thres < thres_min:
			thres = thres_min
			thres_max = thres + param_peak_reactivity


if __name__ == '__main__':
    main()
