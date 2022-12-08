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
    
def move_abs_v(axis, distance, dist_units=Units.LENGTH_MILLIMETRES, wait_until_idle=True, velocity=10, vel_units=Units.VELOCITY_MILLIMETRES_PER_SECOND):
    """
    Mimics the v7 firmware version of axis.move_absolute() for which velocity
    can be specified. Overwrites the max speed of the axis to do this, and does
    not undo it afterwards.
    """
    axis.settings.set("maxspeed", velocity, vel_units)
    axis.move_absolute(distance, dist_units, wait_until_idle=wait_until_idle)
    
def move_rel_v(axis, distance, dist_units=Units.LENGTH_MILLIMETRES, wait_until_idle=True, velocity=10, vel_units=Units.VELOCITY_MILLIMETRES_PER_SECOND):
    """
    Mimics the v7 firmware version of axis.move_relative() for which velocity
    can be specified. Overwrites the max speed of the axis to do this, and does
    not undo it afterwards.
    """
    axis.settings.set("maxspeed", velocity, vel_units)
    axis.move_relative(distance, dist_units, wait_until_idle=wait_until_idle)

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    com = get_port()
    
    #%% Open the connection
    try:
        # Update devices from internet
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
        
    T = 10
    r = 25
    N = 32
    
    v0 = 2*np.pi*r / T
    dt = T / N
    
    circle_r = np.round(r *np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1] * 1j, 6)
    circle_v = np.round(v0*np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1], 6)
    
    # Open a connection to the device
    with Connection.open_serial_port(com) as connection:
        device_list = connection.detect_devices()
        axis1 = device_list[1].get_axis(1)
        axis2 = device_list[2].get_axis(1)
        
        # Centre the stage
        move_abs_v(axis1, 100, velocity=10)
        move_abs_v(axis2, 85, velocity=10)
        
        #%% Trace a circle in 1 axis
        for ii in range(N):
            print("ax1 r: {:.4f}mm; v: {:.4f}mm/s".format(100+np.real(circle_r[ii]), np.abs(np.real(circle_v[ii]))))
            print("ax2 r: {:.4f}mm; v: {:.4f}mm/s".format(100+np.imag(circle_r[ii]), np.abs(np.imag(circle_v[ii]))))
            t1 = time.time_ns()
            # If axis1 doesn't move
            if np.abs(np.real(circle_v[ii])) == 0:
                print("Move axis2")
                move_abs_v(axis2, 100+np.imag(circle_r[ii]), velocity=np.abs(np.imag(circle_v[ii])))
            # If axis2 doesn't move
            elif np.abs(np.imag(circle_v[ii])) == 0:
                print("Move axis 1")
                move_abs_v(axis1, 100+np.real(circle_r[ii]), velocity=np.abs(np.real(circle_v[ii])))
            else:
                print("Move both axes")
                move_abs_v(axis1, 100+np.real(circle_r[ii]), velocity=np.abs(np.real(circle_v[ii])), wait_until_idle=False)
                move_abs_v(axis2, 100+np.imag(circle_r[ii]), velocity=np.abs(np.imag(circle_v[ii])))
            t2 = time.time_ns()
            # print((t2-t1)*10**-9)

