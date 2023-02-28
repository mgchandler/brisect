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
import matplotlib.pyplot as plt
import numpy as np
import sys
from zaber_motion import Library

# Can get rid of this if the package has been installed.
sys.path.append(r"C:\Users\mc16535\OneDrive - University of Bristol\Documents\Postgrad\Coding\brisect")
import brisect as ect
from brisect.handyscope import Handyscope
from brisect.zaberstage import Stage

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    # Get settings from command line or default value.
    if len(sys.argv) > 1:
        if len(sys.argv) > 2:
            raise TypeError("ect-smart-scan: too many arguments.")
        yaml_filename = sys.argv[1]
    # Typically called when running in IDE, or if no arg given from cmd.
    else:
        yaml_filename = "sine.yml"
    
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
            
            ect.geometry_search(handyscope, stage, origin=[78, 67, 10.73], width=60, height=125, snake_separation=20, fuzzy_separation=5)
            
            
            # Do the initial scan - work out the geometry.
            x_data, y_data, out_data = ect.grid_sweep_scan(handyscope, stage, [45 , 120], 70, 70, 0, 20, velocity=5, live_plot=True)
            # Correct for liftoff
            _, _, out_data = ect.correct_liftoff(x_data, y_data, out_data)
            # Fit the grid
            block_geometry = ect.fit_geometry_to_data(x_data, y_data, out_data)
            
            #%% Output the data: #TODO Check that this plotting still works. It should do, but idxs may need adjusting
            if settings["trajectory"]["analysis"].lower() == "rms":
                ect.plot_data(r"output\{}".format(settings["job"]["name"]), x_data, y_data, out_data)
                ect.save_csv(r"output\{}".format(settings["job"]["name"]), x_data, y_data, out_data)
                
            elif settings["trajectory"]["analysis"].lower() == "spec":
                freq = np.fft.rfftfreq(handyscope.scp.record_length, 1/handyscope.scp.sample_frequency)
                export_data = np.empty((out_data.shape[0], len(settings["generator"]["signal"]["frequency"])), dtype=out_data.dtype)
                # Only do the frequencies which we have multiplexed.
                for idx, f in enumerate(settings["generator"]["signal"]["frequency"]):
                    f_idx = np.argmin(np.abs(freq - f))
                    export_data[:, idx] = out_data[:, f_idx]
                    ect.plot_data(r"output\{}".format(settings["job"]["name"]), x_data, x_data, out_data[:, f_idx], zlabel="Frequency Spectrum at {:.1f}MHz".format(f*10**-6))
                ect.save_csv(r"output\{}".format(settings["job"]["name"]), x_data, y_data, export_data, zlabel="spec ", zaxis=settings["generator"]["signal"]["frequency"])