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
import csv
import handyscope as hs
import helpers as h
import libtiepie as ltp
import matplotlib.pyplot as plt
import numpy as np
import scan as sc
import sys
import time
import trajectory as traj
from zaber_motion import Library

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    # Get settings from command line or default value.
    if len(sys.argv) > 1:
        if len(sys.argv) > 2:
            raise TypeError("ect-smart-scan: too many arguments.")
        yaml_filename = sys.argv[1]
    # Typically called when running in IDE, or if no arg given from cmd.
    else:
        yaml_filename = "test_scan.yml"
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
        
    settings = h.read_settings(yaml_filename)
    
    with traj.Stage() as stage:
        with hs.Handyscope.from_yaml(yaml_filename) as handyscope:
            print(handyscope)
            
            # Initialise stage position
            stage.move([settings["trajectory"]["init_x"], settings["trajectory"]["init_y"]], velocity=10, mode="abs", wait_until_idle=True)
            
            x_list = [settings["trajectory"]["coords"][i][0] for i in range(len(settings["trajectory"]["coords"]))]
            y_list = [settings["trajectory"]["coords"][i][1] for i in range(len(settings["trajectory"]["coords"]))]
            # If speed is a single value, replicate it to the same size as x_list and y_list.
            if isinstance(settings["trajectory"]["v"], float):
                v_list = [settings["trajectory"]["v"] for i in range(len(x_list))]
            # If speed is a list of values, check how long it is.
            elif isinstance(settings["trajectory"]["v"], list):
                # If list of speeds is too small, cycle through it until we have the right length.
                if len(settings["trajectory"]["v"]) < len(x_list):
                    v_list = [settings["trajectory"]["v"][i%len(settings["trajectory"]["v"])] for i in range(len(x_list))]
                # If list of speeds too large, only take up to the right length.
                else:
                    v_list = settings["trajectory"]["v"][:len(x_list)]
            # We must have an invalid data type.
            else:
                raise TypeError("Velocity should be a list of floats or a float.")
            
            # Initialise storage arrays
            x_data   = np.empty(0)
            y_data   = np.empty(0)
            rms_data = np.empty(0)
            t1 = time.time_ns() * 1e-9
            for idx, (x, y, v) in enumerate(zip(x_list, y_list, v_list)):
                if idx == 0:
                    x_scan, y_scan, rms_scan = sc.linear_scan_rms(handyscope, stage, [x, y], velocity=v, live_plot=True)
                else:
                    x_scan, y_scan, rms_scan = sc.linear_scan_rms(handyscope, stage, [x, y], velocity=v, live_plot=True, old_val=rms_data)
                x_data   = np.append(x_data, x_scan)
                y_data   = np.append(y_data, y_scan)
                rms_data = np.append(rms_data, rms_scan)
            t2 = time.time_ns() * 1e-9
            print("Total scan time: {:.2f}s".format(t2-t1))
            
            h.save_data(r"output\{}".format(settings["job"]["name"]), x_data, y_data, rms_data)