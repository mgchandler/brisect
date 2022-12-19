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
    else:
        yaml_filename = "test_scan.yml"
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
        
    settings = h.read_settings(yaml_filename)
    
    #TODO: Test that this works when moved into hs.Handyscope class
    # ltp.device_list.update()
    
    with traj.Stage() as stage:
        with hs.Handyscope.from_yaml(yaml_filename) as handyscope:
            # print(handyscope)
            
            # Initialise stage position
            stage.move_abs([settings["trajectory"]["init_x"], settings["trajectory"]["init_y"]], velocity=10, wait_until_idle=True)
            
            x_list = settings["trajectory"]["x"]
            y_list = settings["trajectory"]["y"]
            v_list = settings["trajectory"]["v"]
            x_data   = np.empty(0)
            y_data   = np.empty(0)
            rms_data = np.empty(0)
            for x, y, v in zip(x_list, y_list, v_list):
                x_scan, y_scan, rms_scan = sc.linear_scan_rms(handyscope, stage, [x, y], velocity=v)
                x_data   = np.append(x_data, x_scan)
                y_data   = np.append(y_data, y_scan)
                rms_data = np.append(rms_data, rms_scan)
            
            # Plot in 3D
            fig = plt.figure(figsize=(8,6), dpi=100)
            ax = fig.add_subplot(projection='3d')
            graph = ax.scatter(x_data, y_data, rms_data, c=rms_data)
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("y (mm)")
            ax.set_zlabel("RMS Voltage (V)")
            fig.colorbar(graph)
            plt.savefig(r"output\{} 3D.png".format(settings["job"]["name"]))
            plt.show()