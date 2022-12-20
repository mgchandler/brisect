# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 15:34:27 2022

@author: mc16535

A file containing functions which combine the zaber stage and the handyscope.
"""
# import handyscope as hs
import helpers as h
import matplotlib.pyplot as plt
import numpy as np
import time
# import trajectory as traj
from zaber_motion import Units

def linear_scan_rms(handyscope, stage, target, length_units=Units.LENGTH_MILLIMETRES, velocity=1, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, move_mode="abs", live_plot=False, old_val=None):
    """ Collect data from handyscope while stages move the substrate in a 
    line. """
    # Initialise storage
    x   = []
    y   = []
    val = []
    # Start moving the stage
    stage.move(target, length_units=Units.LENGTH_MILLIMETRES, velocity=velocity, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, mode=move_mode, wait_until_idle=False)

    # Collect the data
    while abs(target[0] - stage.axis2.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution or abs(target[1] - stage.axis1.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution:
        val.append(h.rms(handyscope.get_record()))
        x.append(stage.axis2.get_position(Units.LENGTH_MILLIMETRES))
        y.append(stage.axis1.get_position(Units.LENGTH_MILLIMETRES))
        # Only collect 100 times per second - #TODO will need tweaking depending on velocity.
        # Plotting takes a bit of time, else explicitly sleep for a period of time.
        if live_plot:
            if len(val) < 100:
                if old_val is not None:
                    plt.plot(list(old_val[-100+len(val):]) + val)
                else:
                    plt.plot(val)
            else:
                plt.plot(val[-100:])
            plt.show()
        else:
            time.sleep(.01)
        
    
    return np.asarray(x), np.asarray(y), np.asarray(val)