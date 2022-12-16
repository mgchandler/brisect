# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 16:36:22 2022

@author: mc16535

A file containing classes which wrap around the generator and oscilloscope
classes from libtiepie, to enable compatibility with "with" statements.
"""
from helpers import find_gen, find_scp
import libtiepie as ltp
import libtiepie.api as api
from libtiepie.devicelistitem import DeviceListItem
import time
import warnings

class open_gen:
    def __init__(self, generator_item, frequency, v_amp, signal_type=ltp.ST_SINE, dc_offset=0):
        self.generator   = generator_item
        self.frequency   = frequency
        self.v_amp       = v_amp
        self.signal_type = signal_type
        self.dc_offset   = dc_offset
        self.gen = None
    
    def __enter__(self):
        self.gen = self.generator.open_generator()
        self.gen.signal_type = self.signal_type
        self.gen.frequency   = self.frequency
        self.gen.amplitude   = self.v_amp
        self.gen.offset      = self.dc_offset
        self.gen.output_on   = True
        return self.gen
    
    def __exit__(self, exc_type, exc_value, traceback):
        warnings.warn("Generator is not deleted manually - to reuse the same device later in the program, delete the variable.")
        self.gen = None

class open_scp:
    def __init__(self, oscilloscope_item, frequency, record_length, v_range, measure_mode=ltp.MM_BLOCK, active_channels=-1, channel_coupling=ltp.CK_ACV):
        self.oscilloscope     = oscilloscope_item
        self.frequency        = frequency
        self.v_range          = v_range
        self.record_length    = record_length
        self.measure_mode     = measure_mode
        self.active_channels  = active_channels
        self.channel_coupling = channel_coupling
        self.scp = None
        
    def __enter__(self):
        self.scp                  = self.oscilloscope.open_oscilloscope()
        self.scp.measure_mode     = self.measure_mode
        self.scp.sample_frequency = self.frequency
        self.scp.record_length    = self.record_length
        for idx, ch in enumerate(self.scp.channels):
            if self.active_channels == -1 or idx in self.active_channels:
                ch.enabled  = True
                ch.range    = self.v_range
                ch.coupling = self.channel_coupling
            else:
                ch.enabled  = False
        # scp.trigger_time_out = 1
        # for ch in scp.channels:
        #     ch.trigger.enabled = False
        # ch = scp.channels[0]
        return self.scp
    
    def __exit__(self, exc_type, exc_value, traceback):
        warnings.warn("Oscilloscope is not deleted manually - to reuse the same device later in the program, delete the variable.")
        self.scp = None
        
class Handyscope:
    __slots__ = ('gen', 'scp')
    
    def __init__(self, input_frequency, input_amplitude, output_sample_frequency, output_record_length, output_range, input_signal_type=ltp.ST_SINE, input_offset=0, output_measure_mode=ltp.MM_BLOCK, output_active_channels=-1, output_channel_coupling=ltp.CK_ACV):
        # self._input_frequency         = input_frequency
        # self._input_amplitude         = input_amplitude
        # self._input_signal_type       = input_signal_type
        # self._input_offset            = input_offset
        # self._output_sample_frequency = output_sample_frequency
        # self._output_record_length    = output_record_length
        # self._output_range            = output_range
        # self._output_measure_mode     = output_measure_mode
        # self._output_active_channels  = output_active_channels
        # self._output_channel_coupling = output_channel_coupling
        
        # gen_idx = h.find_gen(ltp.device_list)
        # scp_idx = h.find_scp(ltp.device_list)
        
        self.gen = ltp.device_list.get_item_by_index(find_gen(ltp.device_list)).open_generator()
        self.scp = ltp.device_list.get_item_by_index(find_scp(ltp.device_list)).open_oscilloscope()
        
        self.gen.signal_type = input_signal_type
        self.gen.frequency   = input_frequency
        self.gen.amplitude   = input_amplitude
        self.gen.offset      = input_offset
        self.gen.output_on   = True
        
        self.scp.measure_mode     = output_measure_mode
        self.scp.sample_frequency = output_sample_frequency
        self.scp.record_length    = output_record_length
        for idx, ch in enumerate(self.scp.channels):
            if output_active_channels == -1 or idx in output_active_channels:
                ch.enabled  = True
                ch.range    = output_range
                ch.coupling = output_channel_coupling
            else:
                ch.enabled  = False
    
    def get_record(self):
        self.scp.start()
        self.gen.start()
        
        while not self.scp.is_data_ready:
            time.sleep(.01)
        
        data = self.scp.get_data()
        
        self.gen.stop()
        # self.scp.stop()
        
        return data