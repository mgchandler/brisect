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
import analysis as an
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
        yaml_filename = "test_sine.yml"
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
        
    settings = h.read_settings(yaml_filename)
    
    #%% Start the scan
    with traj.Stage() as stage:
        with hs.Handyscope.from_yaml(yaml_filename) as handyscope:
            print(handyscope)
            
            # Do the initial scan - work out the geometry.
            x_data, y_data, out_data = sc.grid_sweep_scan(handyscope, stage, [45 , 120], 70, 70, 0, 20, velocity=5, live_plot=True)
            # Correct for liftoff
            _, _, out_data = an.correct_liftoff(x_data, y_data, out_data)
            # Fit the grid
            block_geometry = an.fit_geometry_to_data(x_data, y_data, out_data)
            
            #%% Output the data: #TODO Check that this plotting still works. It should do, but idxs may need adjusting
            if settings["trajectory"]["analysis"].lower() == "rms":
                h.plot_data(r"output\{}".format(settings["job"]["name"]), x_data, y_data, out_data)
                h.save_csv(r"output\{}".format(settings["job"]["name"]), x_data, y_data, out_data)
                
            elif settings["trajectory"]["analysis"].lower() == "spec":
                freq = np.fft.rfftfreq(handyscope.scp.record_length, 1/handyscope.scp.sample_frequency)
                export_data = np.empty((out_data.shape[0], len(settings["generator"]["signal"]["frequency"])), dtype=out_data.dtype)
                # Only do the frequencies which we have multiplexed.
                for idx, f in enumerate(settings["generator"]["signal"]["frequency"]):
                    f_idx = np.argmin(np.abs(freq - f))
                    export_data[:, idx] = out_data[:, f_idx]
                    h.plot_data(r"output\{}".format(settings["job"]["name"]), x_data, x_data, out_data[:, f_idx], zlabel="Frequency Spectrum at {:.1f}MHz".format(f*10**-6))
                h.save_csv(r"output\{}".format(settings["job"]["name"]), x_data, y_data, export_data, zlabel="spec ", zaxis=settings["generator"]["signal"]["frequency"])