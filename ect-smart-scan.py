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
import sys
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
    
    ltp.network.auto_detect_enabled = True
    ltp.device_list.update()
    
    gen_idx = h.find_gen(ltp.device_list)
    scp_idx = h.find_scp(ltp.device_list)
    with hs.open_gen(ltp.device_list.get_item_by_index(gen_idx)) as gen:
        print(gen.name)
        print(gen.type)
        with hs.open_scp(ltp.device_list.get_item_by_index(scp_idx)) as scp:
            # Do all the handyscope stuff here
            print(scp.name)
            print(scp.type)