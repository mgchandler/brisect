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
import helpers as h
import trajectory as traj
from zaber_motion import Library
from zaber_motion.ascii import Connection

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    com = h.get_port()
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
        
    T = 10
    r = 25
    N = 32
    
    # Open a connection to the device
    with Connection.open_serial_port(com) as connection:
        device_list = connection.detect_devices()
        axis1 = device_list[1].get_axis(1)
        axis2 = device_list[2].get_axis(1)
        
        traj.circle_polygonal(axis1, axis2, [100, 100], r, N, T)