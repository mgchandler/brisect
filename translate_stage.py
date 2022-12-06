# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 10:14:40 2022

@author: mc16535

(v1) Script for the movement of the Zaber translation stage.
Essentially just a copy-and-paste of Zaber's example script, with automatic
working out which port the device is connected to.

N.B. in device_list, device 0 is the z-axis, device 1 is the y-axis and device
2 is the x-axis.
"""

from serial.tools.list_ports import comports
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection

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

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    com = get_port()
    
    #%% Open the connection
    try:
        # Update devices from internet
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
    
    # Open a connection to the device
    with Connection.open_serial_port(com) as connection:
        device_list = connection.detect_devices()
        print("Found {} devices".format(len(device_list)))
        
        for dd, device in enumerate(device_list):
            axis = device.get_axis(1)
            axis.home()
            print("Device {} streams {}".format(dd+1, device.settings.get('stream.numstreams')))
    
            # # Move to 10mm
            # axis.move_absolute(10, Units.LENGTH_MILLIMETRES)
        
            # # Move by an additional 5mm
            # axis.move_relative(5, Units.LENGTH_MILLIMETRES)