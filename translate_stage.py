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

import numpy as np
from serial.tools.list_ports import comports
import time
from zaber_motion import Units, Library, Measurement
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
        
    T = 15
    r = 30e-3
    N = 18
    
    v0 = 2*np.pi*r / T
    dt = T / N
    
    # Open a connection to the device
    with Connection.open_serial_port(com) as connection:
        device_list = connection.detect_devices()
        print("Found {} devices".format(len(device_list)))
        
        axis1 = device_list[1].get_axis(1)
        axis2 = device_list[2].get_axis(1)
        axis1.home()
        axis2.home()
        axis1.move_absolute(10, Units.LENGTH_CENTIMETRES, wait_until_idle=False)
        axis2.move_absolute(8.5, Units.LENGTH_CENTIMETRES, wait_until_idle=True)
        
        print("doing bad circle")
        
        #%% Test 1: Try a bad circle by changing velocity
        circle = v0*np.exp(2j*np.pi*np.linspace(0, 1, N))
        for dt in range(N):
            axis1.move_velocity(np.real(circle), Units.VELOCITY_CENTIMETRES_PER_SECOND)
            axis2.move_velocity(np.imag(circle), Units.VELOCITY_CENTIMETRES_PER_SECOND)
            time.sleep(dt)
            
        print("setting maxspeed")
        
        #%% Test 2: Try changing maxspeed
        axis1.move_absolute(5, Units.LENGTH_CENTIMETRES, wait_until_idle=False)
        axis2.move_absolute(5, Units.LENGTH_CENTIMETRES, wait_until_idle=True)
        axis1.generic_command("1 set maxspeed 0.1")
        axis2.generic_command("1 set maxspeed 0.1")
        axis1.move_relative(10, Units.LENGTH_CENTIMETRES, wait_until_idle=False)
        axis2.move_relative(10, Units.LENGTH_CENTIMETRES, wait_until_idle=False)
        time.sleep(2)
        axis1.generic_command("1 set maxspeed 0.5")
        axis2.generic_command("1 set maxspeed 0.2")
        time.sleep(2)
        axis1.generic_command("1 set maxspeed 0.1")
        axis2.generic_command("1 set maxspeed 0.1")
        
        axis1.settings.set("maxspeed", .1, Units.VELOCITY_CENTIMETRES_PER_SECOND)