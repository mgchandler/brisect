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
import brisect as ect
from brisect.handyscope import Handyscope
from brisect.zaberstage import Stage
import matplotlib.pyplot as plt
import numpy as np
import sys
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
        yaml_filename = "singlefreq.yml"
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
        
    settings = ect.read_settings(yaml_filename)
    
    #%% Start the scan
    with Stage() as stage:
        with Handyscope.from_yaml(yaml_filename) as handyscope:
            print(handyscope)
            
            # Look for the geometry and trace it out.
            coordinates, rms_data, geom_coords = ect.domain_search(
                handyscope, 
                stage, 
                origin=[settings['trajectory']['init_x'], settings['trajectory']['init_y'], settings['trajectory']['init_z']],
                width=100,
                height=100,
                snake_separation=25,
                fuzzy_separation=5
            )
            
            # We have an approximation for the geometry. Scan within it to look for defects.
            coords, rms_scan, defect_coords = ect.domain_search(
                handyscope,
                stage,
                origin="from geom_coords",
                width="from geom_coords",
                height="from geom_coords",
                snake_separation=5,
                fuzzy_separation=1
            )
            coordinates = np.append(coordinates, coords, axis=1)
            rms_data = np.append(rms_data, rms_scan, axis=1)
            
            # Save the data.
            ect.plot_data(settings["job"]["name"], coords, rms_scan)
            ect.save_csv(settings["job"]["name"], coordinates, rms_data)