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
    def __init__(self, generator_item):
        self.generator = generator_item
    
    def __enter__(self):
        return self.generator.open_generator()
    
    def __exit__(self, exc_type, exc_value, traceback):
        # print(**kwargs)
        self.generator = None

class open_scp:
    def __init__(self, oscilloscope_item):
        self.oscilloscope = oscilloscope_item
    
    def __enter__(self):
        return self.oscilloscope.open_oscilloscope()
    
    def __exit__(self, exc_type, exc_value, traceback):
        # print(**kwargs)
        self.oscilloscope = None