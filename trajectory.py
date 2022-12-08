# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 15:42:02 2022

@author: mc16535
"""
import helpers as h
import numpy as np
from zaber_motion import Units

def move_abs_v(axis, distance, length_units=Units.LENGTH_MILLIMETRES, wait_until_idle=True, velocity=10, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND):
    """
    Mimics the v7 firmware version of axis.move_absolute() for which velocity
    can be specified. Overwrites the max speed of the axis to do this, and does
    not undo it afterwards.
    """
    axis.settings.set("maxspeed", velocity, velocity_units)
    axis.move_absolute(distance, length_units, wait_until_idle=wait_until_idle)
    
def move_rel_v(axis, distance, length_units=Units.LENGTH_MILLIMETRES, wait_until_idle=True, velocity=10, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND):
    """
    Mimics the v7 firmware version of axis.move_relative() for which velocity
    can be specified. Overwrites the max speed of the axis to do this, and does
    not undo it afterwards.
    """
    axis.settings.set("maxspeed", velocity, velocity_units)
    axis.move_relative(distance, length_units, wait_until_idle=wait_until_idle)

def circle_polygonal(axis1, axis2, C, r, N, T, length_units=Units.LENGTH_MILLIMETRES):
    """
    Trace out a circle with two perpendicular axes. Approximates the circle
    with an N-sided polygon. Currently has stop-start behaviour between each
    segment.

    Parameters
    ----------
    axis1 : TYPE
        DESCRIPTION.
    axis2 : TYPE
        DESCRIPTION.
    C : list, array
        Centre position of the circle with units in dist_units.
    r : float
        Radius of the circle with units in dist_units.
    N : int
        Number of lines to discretise the circle into.
    T : float
        Desired total time taken in seconds. Note no checks made to ensure that
        resulting velocity is physical - this is left to the user.
    dist_units : Units, optional
        Units of distance used. The default is Units.LENGTH_MILLIMETRES.
    """
    v0 = 2*np.pi*r / T
    circle_r = np.round(r *np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1] * 1j, 6)
    circle_v = np.round(v0*np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1], 6)
    
    vel_units = h.velocity_units(length_units)
    
    axis1.move_absolute(C[1], length_units)
    axis2.move_absolute(C[0]+r, length_units)
    for ii in range(N):
        # If axis1 doesn't move
        if np.abs(np.real(circle_v[ii])) == 0:
            move_abs_v(axis2, C[0]+np.imag(circle_r[ii]), velocity=np.abs(np.imag(circle_v[ii])), velocity_units=vel_units)
        # If axis2 doesn't move
        elif np.abs(np.imag(circle_v[ii])) == 0:
            move_abs_v(axis1, C[1]+np.real(circle_r[ii]), velocity=np.abs(np.real(circle_v[ii])), velocity_units=vel_units)
        # Then both must move
        else:
            move_abs_v(axis1, C[1]+np.real(circle_r[ii]), velocity=np.abs(np.real(circle_v[ii])), velocity_units=vel_units, wait_until_idle=False)
            move_abs_v(axis2, C[0]+np.imag(circle_r[ii]), velocity=np.abs(np.imag(circle_v[ii])), velocity_units=vel_units)
