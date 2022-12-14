# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 16:36:22 2022

@author: mc16535

A file containing classes which wrap around the generator and oscilloscope
classes from libtiepie, to enable compatibility with "with" statements.
"""
import libtiepie as ltp
from libtiepie.devicelistitem import DeviceListItem

class open_gen:
    def __init__(self, generator_item, frequency, v_amp, signal_type=ltp.ST_SINE, dc_offset=0):
        self.generator   = generator_item
        self.frequency   = frequency
        self.v_amp       = v_amp
        self.signal_type = signal_type
        self.dc_offset   = dc_offset
    
    def __enter__(self):
        gen = self.generator.open_generator()
        gen.signal_type = self.signal_type
        gen.frequency   = self.frequency
        gen.amplitude   = self.v_amp
        gen.offset      = self.dc_offset
        gen.output_on   = True
        return gen
    
    def __exit__(self, exc_type, exc_value, traceback):
        # print(**kwargs)
        self.generator = None

class open_scp:
    def __init__(self, oscilloscope_item, frequency, record_length, v_range, measure_mode=ltp.MM_BLOCK, active_channels=-1, channel_coupling=ltp.CK_ACV):
        self.oscilloscope     = oscilloscope_item
        self.frequency        = frequency
        self.v_range          = v_range
        self.record_length    = record_length
        self.measure_mode     = measure_mode
        self.active_channels  = active_channels
        self.channel_coupling = channel_coupling
        
    def __enter__(self):
        scp                  = self.oscilloscope.open_oscilloscope()
        scp.measure_mode     = self.measure_mode
        scp.sample_frequency = self.frequency
        scp.record_length    = self.record_length
        for idx, ch in enumerate(scp.channels):
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
        return scp
    
    def __exit__(self, exc_type, exc_value, traceback):
        # print(**kwargs)
        self.oscilloscope = None