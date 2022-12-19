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
    
    gen_freq = 13.5e6
    sample_freq = 5e8
    record_length = 50000
    
    target = 75
    
    with Connection.open_serial_port(com) as connection:
        device_list = connection.detect_devices()
        axis1 = device_list[1].get_axis(1)
        axis2 = device_list[2].get_axis(1)
        
        with hs.Handyscope(gen_freq, 0.1, sample_freq, record_length, 1, output_resolution=12, output_active_channels=0) as handyscope:#, output_active_channels=0
            print(handyscope)
            np_data = np.asarray(handyscope.get_record())
            t = np.linspace(0, (handyscope.scp.record_length-1) / handyscope.scp.sample_frequency, int(handyscope.scp.record_length))
            
            traj.move_abs_v(axis1, 51)
            traj.move_abs_v(axis2, 140)
            traj.move_abs_v(axis2, target, velocity=2, wait_until_idle=False)  
            
            t_data   = []
            d_data   = []
            rms_data = []
            start_time = time.time_ns()*10**-9
            try:
                while abs(target - axis2.get_position(Units.LENGTH_MILLIMETRES)) > 1e-5:
                    np_data = np.asarray(handyscope.get_record())
                    t_data.append(time.time_ns()*10**-9 - start_time)
                    d_data.append(axis2.get_position(Units.LENGTH_MILLIMETRES))
                    rms_val = h.rms(np_data[0, :])
                    rms_data.append(rms_val)
                    
                    plt.plot(d_data, rms_data)
                    plt.xlabel("Position (mm)")
                    plt.ylabel("RMS Voltage (V)")
                    plt.title("Gen Freq {:.3f}MHz - Amp {:.3f}V".format(handyscope.gen.frequency*10**-6, handyscope.gen.amplitude))
                    plt.show()
            except KeyboardInterrupt:
                plt.figure()
                plt.plot(d_data, rms_data)
                plt.xlabel("Position (mm)")
                plt.ylabel("RMS Voltage (V)")
                plt.title("Gen Freq {:.3f}MHz - Amp {:.3f}V".format(handyscope.gen.frequency*10**-6, handyscope.gen.amplitude))
                plt.show()
                raise KeyboardInterrupt