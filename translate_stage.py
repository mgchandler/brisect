# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 10:14:40 2022

@author: mc16535

(v1) Script for the movement of the Zaber translation stage.
Essentially just a copy-and-paste of Zaber's example script, with automatic
working out which port the device is connected to.
"""

import serial.tools.list_ports as lp
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection

def get_port(manufacturer="FTDI"):
    """
    Returns the port which the device of interest is connected to. Serial does
    not guarantee that comports() returns ports in order, thus we sort by port.
    Only the first port which has the right manufacturer is retured; if none
    present then RuntimeError is raised.
    """
    ports = sorted(lp.comports(), key=lambda port: port.device)
    for port in ports:
        if port.manufacturer == manufacturer:
            return port.device
    raise RuntimeError("Device cannot be found! Connect it and make sure drivers are installed.")

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    #%% Find which port we are connected to
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
    
        device = device_list[0]
    
        axis = device.get_axis(1)
        if not axis.is_homed():
          axis.home()
    
        # Move to 10mm
        axis.move_absolute(10, Units.LENGTH_MILLIMETRES)
    
        # Move by an additional 5mm
        axis.move_relative(5, Units.LENGTH_MILLIMETRES)