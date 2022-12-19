# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 15:30:00 2022

@author: mc16535

A file containing helper functions for ect-smart-scan, which do not belong in
any other file. Should consist of short, easily read functions, rather than
anything too much more extensive.
"""
import libtiepie as ltp
import numpy as np
from serial.tools.list_ports import comports
from zaber_motion import Units
import yaml

def get_port(manufacturer="FTDI"):
    """
    Returns the port which the device of interest is connected to. Serial does
    not guarantee that comports() returns ports in order, thus we sort by port.
    It is assumed that only one connection is available, thus the first one is
    returned; if none available then RuntimeError raised.
    """
    ports = sorted(comports(), key=lambda port: port.device)
    for port in ports:
        if port.manufacturer == manufacturer:
            return port.device
    raise RuntimeError("Device cannot be found! Connect it and make sure drivers are installed.")

def velocity_units(length_units):
    """
    Returns the equivalent units of velocity for the supplied length units.
    """
    if length_units == Units.LENGTH_METRES:
        return Units.VELOCITY_METRES_PER_SECOND
    elif length_units == Units.LENGTH_CENTIMETRES:
        return Units.VELOCITY_CENTIMETRES_PER_SECOND
    elif length_units == Units.LENGTH_MILLIMETRES:
        return Units.VELOCITY_MILLIMETRES_PER_SECOND
    elif length_units == Units.LENGTH_MICROMETRES:
        return Units.VELOCITY_MICROMETRES_PER_SECOND
    elif length_units == Units.LENGTH_NANOMETRES:
        return Units.VELOCITY_NANOMETRES_PER_SECOND
    elif length_units == Units.LENGTH_INCHES:
        return Units.VELOCITY_INCHES_PER_SECOND
    else:
        raise TypeError("Length units are invalid")

# def convert_units(value, unit1, unit2):
#     """
#     Convert the value given in unit1 into its equivalent result in unit2.
#     """
#     if unit1 == Units.

def find_gen(device_list):
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

def find_scp(device_list):
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

def rms(x):
    """
    Compute the root-mean-square of a numpy vector.
    """
    return np.sqrt(np.mean(np.asarray(x)**2))

def read_settings(filename):
    with open(filename, 'r') as file:
        settings = yaml.safe_load(file)
    return settings