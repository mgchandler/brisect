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
import trajectory as traj
from zaber_motion import Units

def grid_sweep_scan(handyscope, stage, origin, width, height, rotation, separation, length_units=Units.LENGTH_MILLIMETRES, velocity=1, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, live_plot=False):
    """
    Collect RMS data from handyscope while the stage sweeps out a grid. Grid is
    defined by the origin (i.e. bottom-left corner), width and height in the x-
    and y-axes, rotation of the rectangle about the origin, and passes in the
    grid have some separation.
    (N.B. the grid will have square `cells` apart from at the edges, which will
     be squashed slightly. Tailor "separation" to minimise this effect.)

    Parameters
    ----------
    handyscope : Handyscope obj
        Handyscope object from module `handyscope`. Should already have been
        initialised.
    stage : Stage obj
        Stage object from module `trajectory`. Should already have been
        initialised.
    origin : array-like (2,)
        x- and y-coordinates of the origin of the grid. Assumed to be the
        bottom-left corner of the grid.
    width : float
        Full width of the grid in the x-axis (i.e. before rotation).
    height : float
        Full height of the grid in the y-axis (before rotation).
    rotation : float
        Rotation of the grid (radians) about the origin.
    separation : float
        Distance which separates rows and columns. Each `cell` in the grid
        should look square.
    length_units : Length Units, optional
        Units in which all distances are provided. The default is
        Units.LENGTH_MILLIMETRES.
    velocity : float, optional
        Speed which will be used to perform the sweep. The default is 1.
    velocity_units : Velocity Units, optional
        Units which velocity is provided. The default is
        Units.VELOCITY_MILLIMETRES_PER_SECOND.

    Returns
    -------
    x_data : ndarray (N,)
        x-coordinates of the scan contained in rms_data.
    y_data : ndarray (N,)
        y-coordinates of the scan contained in rms_data.
    rms_data : ndarray (N,)
        RMS voltage obtained from the scan around the grid.
    """
    origin = np.squeeze(origin)
    if origin.shape != (2,):
        raise ValueError("scan.grid_sweep_scan: origin must be 2D coordinates.")
    # Determine coordinates of the grid
    coords = traj.grid_sweep_coords(separation, origin[0], origin[1], width, height, rotation)
    
    # Initialise position. Will be absolute and we need it to wait until it arrives.
    stage.move(coords[0, :], length_units=length_units, velocity=velocity, velocity_units=velocity_units)
    # Start the scan.
    rms_data = None
    for idx, step in enumerate(coords):
        # Do the scan
        if live_plot:
            x_scan, y_scan, rms_scan = linear_scan_rms(handyscope, stage, step, length_units=length_units, velocity=velocity, velocity_units=velocity_units, live_plot=live_plot, old_val=rms_data)
        else:
            x_scan, y_scan, rms_scan = linear_scan_rms(handyscope, stage, step, length_units=length_units, velocity=velocity, velocity_units=velocity_units)
        
        # Save the data.
        if idx == 0:
            #Initialise output arrays
            x_data = x_scan
            y_data = y_scan
            rms_data = rms_scan
        else:
            # Append data
            x_data   = np.append(x_data, x_scan)
            y_data   = np.append(y_data, y_scan)
            rms_data = np.append(rms_data, np.asarray(rms_scan), axis=0)
    
    return x_data, y_data, rms_data

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