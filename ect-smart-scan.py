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
from zaber_motion import Library
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
        
    T = 10
    r = 25
    N = 32
    
    gen_freq = 10e3
    n_cycles = 5
    n_samples_per_cycle = 10
    sample_freq = int(gen_freq * n_samples_per_cycle)
    record_length = int(n_cycles * sample_freq / gen_freq)
    
    # ltp.network.auto_detect_enabled = True
    ltp.device_list.update()
    
    gen_idx = h.find_gen(ltp.device_list)
    scp_idx = h.find_scp(ltp.device_list)
    with hs.open_gen(ltp.device_list.get_item_by_index(gen_idx), gen_freq, 0.1) as gen:
        print(gen.name)
        print(gen.type)
        with hs.open_scp(ltp.device_list.get_item_by_index(scp_idx), sample_freq, record_length, 4) as scp:
            # Do all the handyscope stuff here
            print(scp.name)
            print(scp.type)
            
            # gen.signal_type = ltp.ST_SINE
            # gen.frequency = gen_freq
            # gen.amplitude = 0.1
            # gen.offset = 0
            # gen.output_on = True
            
            # scp.measure_mode = ltp.MM_BLOCK
            # scp.sample_frequency = sample_freq
            # scp.record_length = record_length
            # # scp.pre_sample_ratio = 0
            # for ch in scp.channels:
            #     ch.enabled = True
            #     ch.range = 4
            #     ch.coupling = ltp.CK_ACV
            # scp.trigger_time_out = 1
            # for ch in scp.channels:
            #     ch.trigger.enabled = False
            # ch = scp.channels[0]
            # # ch.trigger.kind = ltp.TK_RISINGEDGE
            # # ch.trigger.hystereses[0]
            
            scp.start()
            gen.start()
            
            while not scp.is_data_ready:
                time.sleep(.01)
            
            data = scp.get_data()
            
            gen.stop()
            
            np_data = np.asarray(data)
            t = np.linspace(0, n_cycles / gen_freq, record_length)
            plt.plot(t * 1e6, np_data[0, :])
            plt.xlabel("Time (us)")
            plt.ylabel("Voltage (V)")
            plt.show()
