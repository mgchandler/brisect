# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 15:34:27 2022

@author: mc16535

A file containing functions which combine the zaber stage and the handyscope.
"""
# import handyscope as hs
import helpers as h
import numpy as np
# import trajectory as traj
from zaber_motion import Units

def linear_scan_rms(handyscope, stage, target, length_units=Units.LENGTH_MILLIMETRES, velocity=1, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, move_mode="abs"):
    """ Collect data from handyscope while stages move the substrate in a 
    line. """
    # Initialise storage
    x   = []
    y   = []
    val = []
    # Start moving the stage
    if move_mode == "abs":
        stage.move_abs(target, length_units=Units.LENGTH_MILLIMETRES, velocity=velocity, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, wait_until_idle=False)
    elif move_mode == "rel":
        stage.move_rel(target, length_units=Units.LENGTH_MILLIMETRES, velocity=velocity, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, wait_until_idle=False)
    else:
        raise NotImplementedError("Movement mode should be 'abs' or 'rel'.")
    
    # Collect the data
    while abs(target[0] - stage.axis2.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution or abs(target[1] - stage.axis1.get_position(Units.LENGTH_MILLIMETRES)) > stage.mm_resolution:
        val.append(h.rms(handyscope.get_record()))
        x.append(stage.axis2.get_position(Units.LENGTH_MILLIMETRES))
        y.append(stage.axis1.get_position(Units.LENGTH_MILLIMETRES))
    
    return np.asarray(x), np.asarray(y), np.asarray(val)