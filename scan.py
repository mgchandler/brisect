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
    """ 
    Collect RMS data from handyscope while stages move the substrate in a 
    line.
    """
    # Initialise storage
    x   = []
    y   = []
    rms = []
    # Start moving the stage
    stage.move(target, length_units=Units.LENGTH_MILLIMETRES, velocity=velocity, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, mode=move_mode, wait_until_idle=False)

    # Collect the data
    while abs(target[0] - stage.axis2.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution or abs(target[1] - stage.axis1.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution:
        rms.append(h.rms(handyscope.get_record()))
        x.append(stage.axis2.get_position(Units.LENGTH_MILLIMETRES))
        y.append(stage.axis1.get_position(Units.LENGTH_MILLIMETRES))
        # Only collect 100 times per second - #TODO will need tweaking depending on velocity.
        # Plotting takes a bit of time, else explicitly sleep for a period of time.
        if live_plot:
            if len(rms) < 100:
                if old_val is not None:
                    plt.plot(list(old_val[-100+len(rms):]) + rms)
                else:
                    plt.plot(rms)
            else:
                plt.plot(rms[-100:])
            plt.show()
        else:
            time.sleep(.01)
        
    return np.asarray(x), np.asarray(y), np.asarray(rms)

def linear_scan_spec(handyscope, stage, target, length_units=Units.LENGTH_MILLIMETRES, velocity=1, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, move_mode="abs", live_plot=False, freq_range=None):
    """
    Collect spectral data from handyscope while stages move the subtrate. Note
    that frequency is not passed out - the user must compute this themselves.
    """
    # Initialise storage
    x    = []
    y    = []
    spec = []
    freq = np.fft.rfftfreq(handyscope.scp.record_length, 1/handyscope.scp.sample_frequency)
    # Start moving the stage
    stage.move(target, length_units=Units.LENGTH_MILLIMETRES, velocity=velocity, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, mode=move_mode, wait_until_idle=False)
    
    if live_plot and freq_range is not None:
        f1 = np.argmin(np.abs(freq - freq_range[0]))
        f2 = np.argmin(np.abs(freq - freq_range[1]))
    # Collect the data
    while abs(target[0] - stage.axis2.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution or abs(target[1] - stage.axis1.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution:
        spec.append(np.fft.rfft(handyscope.get_record()[0, :]))
        x.append(stage.axis2.get_position(Units.LENGTH_MILLIMETRES))
        y.append(stage.axis1.get_position(Units.LENGTH_MILLIMETRES))
        # Only collect 100 times per second - #TODO will need tweaking depending on velocity.
        # Plotting takes a bit of time, else explicitly sleep for a period of time.
        if live_plot:
            fig = plt.figure(figsize=(12,5),dpi=100)
            ax1 = fig.add_subplot(111)
            ax1.plot(freq*1e-6, np.abs(spec[-1]))
            if freq_range is not None:
                ax2 = fig.add_axes([.35, .25, .525, .6])
                ax2.plot(freq[f1:f2]*1e-6, np.abs(spec[-1][f1:f2]))
            plt.show(block=False)
        else:
            time.sleep(.01)
    
    return x, y, spec