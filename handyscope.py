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
import numpy as np
import time
import warnings

gen_dict  = {'input_frequency':'frequency',
             'input_amplitude':'amplitude',
             'input_signal_type':'signal_type',
             'input_offset':'offset'}
scp_dict  = {'output_sample_frequency':'sample_frequency',
             'output_record_length':'record_length',
             'output_measure_mode':'measure_mode',
             'output_resolution':'resolution'}
        
class Handyscope:
    __slots__ = ('gen', 'scp')
    
    def __init__(self, input_frequency, input_amplitude, output_sample_frequency, output_record_length, output_range, input_signal_type=ltp.ST_SINE, input_offset=0, output_measure_mode=ltp.MM_BLOCK, output_resolution=12, output_active_channels=-1, output_channel_coupling=ltp.CK_ACV):
        self.gen = ltp.device_list.get_item_by_index(find_gen(ltp.device_list)).open_generator()
        self.scp = ltp.device_list.get_item_by_index(find_scp(ltp.device_list)).open_oscilloscope()
        
        self.gen.signal_type = input_signal_type
        self.gen.frequency   = input_frequency
        self.gen.amplitude   = input_amplitude
        self.gen.offset      = input_offset
        self.gen.output_on   = True
        
        if not isinstance(output_active_channels, list):
            output_active_channels = [output_active_channels]
        for idx, ch in enumerate(self.scp.channels):
            if output_active_channels[0] == -1 or idx in output_active_channels:
                ch.enabled  = True
                ch.range    = output_range
                ch.coupling = output_channel_coupling
            else:
                ch.enabled  = False
        self.scp.sample_frequency = output_sample_frequency
        self.scp.measure_mode     = output_measure_mode
        self.scp.resolution       = output_resolution
        self.scp.record_length    = int(output_record_length)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        del self.gen, self.scp
    
    def __str__(self):
        s  = "Handyscope:\n"
        s += "\tGenerator:\n"
        s += "\t\tFrequency:     {:12.6e}Hz (min: {:12.6e}Hz; max: {:12.6e}Hz)\n".format(self.gen.frequency, self.gen.frequency_min, self.gen.frequency_max)
        s += "\t\tAmplitude:     {:12.3e} V (min: {:12.3e} V; max: {:12.3e}V)\n".format(self.gen.amplitude, self.gen.amplitude_min, self.gen.amplitude_max)
        s += "\tOscilloscope:\n"
        s += "\t\tSample Freq:   {:12.6e}Hz (max: {:12.6e}Hz)\n".format(self.scp.sample_frequency, self.scp.sample_frequency_max)
        s += "\t\tRecord Length: {:8}       (max: {:8})\n".format(self.scp.record_length, self.scp.record_length_max)
        s += "\t\tResolution:    {:8}\n".format(self.scp.resolution)
        s += "\t\tRange:         {:12.3e} V\n".format(self.scp.channels[0].range)
        return s
    
    def new_params(self, **kwargs):
        for kw in kwargs.keys():
            if kw in gen_dict.keys():
                self.gen.__setattr__(gen_dict[kw], kwargs[kw])
            elif kw in scp_dict.keys():
                self.scp.__setattr__(scp_dict[kw], kwargs[kw])
            elif kw == "output_active_channels":
                for idx, ch in enumerate(self.scp.channels):
                    if kwargs[kw] == -1 or idx in kwargs[kw]:
                        ch.enabled = True
                    else:
                        ch.enabled = False
            elif kw == "output_range":
                for idx, ch in enumerate(self.scp.channels):
                    ch.range = kwargs[kw]
            elif kw == "output_channel_coupling":
                for idx, ch in enumerate(self.scp.channels):
                    ch.coupling = kwargs[kw]
    
    def get_record(self, channels=[-1]):
        self.scp.start()
        self.gen.start()
        
        while not self.scp.is_data_ready:
            time.sleep(.01)
        
        data = self.scp.get_data()
        
        self.gen.stop()
        
        # Return all active channels.
        if channels[0] == -1:
            np_data = np.empty((sum(self.scp._active_channels), self.scp.record_length))
            idx = 0
            for ch, active in enumerate(self.scp._active_channels):
                if active:
                    np_data[idx, :] = np.asarray(data[ch])
                    idx += 1
            return np_data
        # Return the requested channels, even if inactive.
        else:
            np_data = np.empty((len(channels), self.scp.record_length))
            for idx, ch in enumerate(channels):
                if self.scp._active_channels[ch]:
                    np_data[idx, :] = np.asarray(data[ch])
                else:
                    np_data[idx, :] = np.zeros((self.scp.record_length))
                    
            return np.asarray(data)