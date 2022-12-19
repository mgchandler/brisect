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
import warnings
from zaber_motion import Library, Units
from zaber_motion.ascii import Connection

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    try:
        com = h.get_port()
    except RuntimeError:
        warnings.warn("Zaber port not found - proceeding without")
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
    
    # ltp.network.auto_detect_enabled = True
    ltp.device_list.update()
    
    # gen_freq = 13.5e6
    # sample_freq = 5e8
    # record_length = 50000
    
    target = 75
    
    settings = h.read_settings("test_scan.yml")
    gen_freq      = float(settings["generator"]["signal"]["frequency"])
    amplitude     = float(settings["generator"]["amplitude"])
    sample_freq   = float(settings["oscilloscope"]["frequency"])
    record_length = int(settings["oscilloscope"]["record_length"])
    
    with traj.Stage() as stage:
        with hs.Handyscope(gen_freq, amplitude, sample_freq, record_length, 1, output_active_channels=0) as handyscope:#, output_active_channels=0
            print(handyscope)
            np_data = np.asarray(handyscope.get_record())
            t = np.linspace(0, (handyscope.scp.record_length-1) / handyscope.scp.sample_frequency, int(handyscope.scp.record_length))
            
            stage.move_abs([settings["trajectory"]["init_x"], settings["trajectory"]["init_y"]], velocity=10, wait_until_idle=True)
            
            all_x, all_y, all_rms = [], [], []
            for idx, (x, y, v) in enumerate(zip(settings["trajectory"]["x"], settings["trajectory"]["y"], settings["trajectory"]["v"])):
                x_data, y_data, rms_data = sc.linear_scan_rms(handyscope, stage, [x, y], velocity=v)
                all_x.append(x_data)
                all_y.append(y_data)
                all_rms.append(rms_data)
            
            all_x_new = all_x[0]
            all_y_new = all_y[0]
            all_rms_new = all_rms[0]
            for i in range(len(all_rms)-1):
                all_x_new = np.append(all_x_new, all_x[i+1])
                all_y_new = np.append(all_y_new, all_y[i+1])
                all_rms_new = np.append(all_rms_new, all_rms[i+1])
            fig = plt.figure(figsize=(8,6), dpi=100)
            ax = fig.add_subplot(projection='3d')
            ax.scatter(all_x_new, all_y_new, all_rms_new)
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("y (mm)")
            ax.set_zlabel("RMS Voltage (V)")
            plt.show()
            plt.figure(figsize=(8,6), dpi=100)
            plt.scatter(all_x_new, all_y_new, c=all_rms_new)
            plt.xlabel("x (mm)")
            plt.ylabel("y (mm)")
            plt.colorbar(label="RMS Voltage (V)")
            plt.show()
            # ax.set_zlim(0.7, .8)