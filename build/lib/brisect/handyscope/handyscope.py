# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 16:36:22 2022

@author: mc16535

A file containing wrappers for libtiepie's Generator and Oscilloscope classes.
Enables single-command usage with the handyscope, for which both generator and
oscilloscope are contained within one object.
"""
import array
from brisect import read_settings
import libtiepie as ltp
import numpy as np
import os
import time

gen_dict  = {'input_frequency':'frequency',
             'input_amplitude':'amplitude',
             'input_signal_type':'signal_type',
             'input_offset':'offset'}
scp_dict  = {'output_sample_frequency':'sample_frequency',
             'output_record_length':'record_length',
             'output_measure_mode':'measure_mode',
             'output_resolution':'resolution'}
mode_dict = {'ST_SINE':ltp.ST_SINE,
             'ST_ARBITRARY':ltp.ST_ARBITRARY,
             'MM_BLOCK':ltp.MM_BLOCK,
             'CK_ACV':ltp.CK_ACV,
             'CK_OHM':ltp.CK_OHM}
        
class Handyscope:
    """
    Container for libtiepie's Generator and Oscilloscope classes. Use as a
    context manager for "with" statements supported, as well as automatically
    reading data without additional setup.
    """
    #%% Attributes
    __slots__ = ('gen', 'scp')
    
    #%% Initialisation function.
    def __init__(self,
            input_frequency: float,
            input_amplitude: float,
            output_sample_frequency: float,
            output_record_length: int,
            output_range: float,
            input_signal_type: int = ltp.ST_SINE,
            input_offset: float = 0,
            output_measure_mode: int = ltp.MM_BLOCK,
            output_resolution: int = 12,
            output_active_channels: list[int] = -1,
            output_channel_coupling: int = ltp.CK_ACV
        ):
        ltp.device_list.update()
        self.gen = ltp.device_list.get_item_by_index(find_gen(ltp.device_list)).open_generator()
        self.scp = ltp.device_list.get_item_by_index(find_scp(ltp.device_list)).open_oscilloscope()
        
        #%% Initialise oscilloscope. We'll probably need sample_frequency for 
        # everything, so start with the scope.
        
        # Do all the channel stuff first, to ensure that sample_frequency is 
        # what we want it to be later.
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
        
        #%% Initialise generator.
        if isinstance(input_signal_type, str):
            self.gen.signal_type = mode_dict[input_signal_type]
        else:
            self.gen.signal_type = input_signal_type
        
        if input_signal_type == ltp.ST_SINE:
            if not isinstance(input_frequency, float):
                raise TypeError("Input frequency must be a float for sine signal generation")
            self.gen.frequency = input_frequency
            
        elif input_signal_type == ltp.ST_ARBITRARY:
            if not isinstance(input_frequency, list):
                raise TypeError("Input frequency must be a list of floats for arbitrary signal generation")
            if len(input_amplitude) != len(input_frequency):
                if len(input_amplitude) < len(input_frequency):
                    input_amplitude = [input_amplitude[i%len(input_amplitude)] for i in range(len(input_frequency))]
                else:
                    input_amplitude = input_amplitude[:len(input_frequency)]
                    
            self.gen.frequency_mode = ltp.FM_SAMPLEFREQUENCY
            self.gen.frequency = self.scp.sample_frequency
            pts = np.linspace(0, (self.scp.record_length-1)/self.gen.frequency, self.scp.record_length)
            sig = np.zeros(self.scp.record_length)
            for amp, freq in zip(input_amplitude, input_frequency):
                sig += amp * np.sin(2*np.pi*freq * pts)
            self.gen.set_data(array.array('f', sig))
        else:
            raise NotImplementedError("Currently only sine and arbitrary signals are supported.")
        self.gen.amplitude   = np.max(input_amplitude)
        self.gen.offset      = input_offset
        self.gen.output_on   = True
        
    #%% Initialisation classmethod.
    @classmethod
    def from_yaml(cls, filename: str):
        """
        Class method for Handyscope. Pass in either the filename (incl. path)
        to the .yaml file containing the settings, or a default value included
        in the `brisect` package. Defaults are `sine.yml` and `multiplex.yml`.

        Parameters
        ----------
        filename : str
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        settings = read_settings(filename)
            
        return cls(
            settings["generator"]["signal"]["frequency"],
            settings["generator"]["signal"]["amplitude"],
            settings["oscilloscope"]["frequency"],
            settings["oscilloscope"]["record_length"],
            settings["oscilloscope"]["range"],
            input_signal_type       = mode_dict[settings["generator"]["signal"]["type"]],
            input_offset            = settings["generator"]["offset"],
            output_measure_mode     = mode_dict[settings["oscilloscope"]["mode"]],
            output_resolution       = settings["oscilloscope"]["resolution"],
            output_active_channels  = settings["oscilloscope"]["active_channels"],
            output_channel_coupling = mode_dict[settings["oscilloscope"]["coupling"]]
        )
    
    #%% Dunder methods
    def __enter__(self):
        """
        Do the setup and return.
        """
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close the connections.
        """
        del self.gen, self.scp
    
    def __str__(self):
        """
        Display all the relevant information.
        """
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
    
    #%% Methods
    def new_params(self, **kwargs):
        """ 
        Reinitialise with new settings.
        """
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
    
    def get_record(self, channels: list[int] = [-1]):
        """ Do all the data collection, so initialisation required outside. """
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



#%% libtiepie helper functions.
def find_gen(device_list: list):
    """
    Returns the index of the item in device_list which corresponds to a
    generator.
    """
    for idx, item in enumerate(device_list):
        if item.can_open(ltp.DEVICETYPE_GENERATOR):
            gen = item.open_generator()
            if gen.signal_types and ltp.ST_ARBITRARY:
                # del gen
                return idx
    return None

def find_scp(device_list: list):
    """
    Returns the index of the item in device_list which corresponds to a
    oscilloscope.
    """
    for idx, item in enumerate(device_list):
        if item.can_open(ltp.DEVICETYPE_OSCILLOSCOPE):
            scp = item.open_oscilloscope()
            if scp.measure_modes and ltp.MM_BLOCK:
                # del scp
                return idx
    return None