# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 15:42:02 2022

@author: mc16535

A file containing Stage class which wraps around zaber_motion containing axis1 
(y) and axis2 (x), assuming firmware v6. Also contains some helper functions.
"""
import helpers as h
import numpy as np
import time
from zaber_motion import Units
from zaber_motion.ascii import Connection

class Stage:
    __slots__ = ("connection", "axis1", "axis2", "mm_resolution")
    
    def __init__(self, port=None, initial_position=None, length_units=Units.LENGTH_MILLIMETRES):
        if port is None:
            port = h.get_port()
        self.connection = Connection.open_serial_port(port)
        device_list = self.connection.detect_devices()
        
        self.axis1 = device_list[1].get_axis(1)
        self.axis2 = device_list[2].get_axis(1)
        
        if initial_position is not None:
            initial_position = np.squeeze(initial_position)
            if initial_position.shape != (2,):
                raise ValueError("Stage: initial_position should be a list of two coordinates")
            self.move_abs(initial_position, length_units=length_units)
        
        self.mm_resolution = 1e-4
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
    
    def __str__(self):
        s  = "Zaber motion stage\n"
        s += "\tAxis1:\n"
        s += "\t\tPosition: {:9.6f}mm\n".format(self.axis1.get_position())
        s += "\tAxis2:\n"
        s += "\t\tPosition: {:9.6f}mm\n".format(self.axis2.get_position())
        return s
    
    def move_x(self, distance, length_units=Units.LENGTH_MILLIMETRES, velocity=10, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, mode="abs", wait_until_idle=True):
        """
        Mimics the v7 firmware version of axis.move_absolute() for which
        velocity can be specified. Overwrites the max speed of the axis to do
        this, and does not undo it afterwards.
        """
        axis2 = self.axis2
        axis2.settings.set("maxspeed", velocity, velocity_units)
        if mode == "abs":
            axis2.move_absolute(distance, length_units, wait_until_idle=wait_until_idle)
        elif mode == "rel":
            axis2.move_relative(distance, length_units, wait_until_idle=wait_until_idle)
        else:
            raise ValueError("Movement mode should be 'abs' or 'rel'.")
        
    def move_y(self, distance, length_units=Units.LENGTH_MILLIMETRES, velocity=10, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, mode="abs", wait_until_idle=True):
        """
        Mimics the v7 firmware version of axis.move_absolute() for which
        velocity can be specified. Overwrites the max speed of the axis to do
        this, and does not undo it afterwards.
        """
        axis1 = self.axis1
        axis1.settings.set("maxspeed", velocity, velocity_units)
        if mode == "abs":
            axis1.move_absolute(distance, length_units, wait_until_idle=wait_until_idle)
        elif mode == "rel":
            axis1.move_relative(distance, length_units, wait_until_idle=wait_until_idle)
        else:
            raise ValueError("Movement mode should be 'abs' or 'rel'.")
    
    def move(self, coords, length_units=Units.LENGTH_MILLIMETRES, velocity=10, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, mode="abs", wait_until_idle=True):
        """
        Move the stage to a set of coordinates (x, y) - these can either be in
        the absolute axis coordinates, or relative to the current position.
        Velocity is taken to mean the total velocity that the stage moves in
        the x- and y-directions, i.e. velocity=sqrt(v_x^2 + v_y^2)
        """
        coords = np.squeeze(coords)
        if coords.shape != (2,):
            raise TypeError("Stage.move_abs(): coordinates must be supplied as two floats.")
            
        # Convert velocity into displacement units.
        if velocity_units != h.velocity_units(length_units):
            native_value = self.axis1.settings.convert_to_native_units("vel", velocity, velocity_units)
            velocity = self.axis1.settings.convert_from_native_units("vel", native_value, h.velocity_units(length_units))
            velocity_units = h.velocity_units(length_units)
        
        # Compute components of velocity in x- and y-directions.
        if mode == "abs":
            old_coords = np.asarray([self.axis2.get_position(), self.axis1.get_position()])
            relative_disp = np.abs(coords - old_coords) # Component-wise distance
        elif mode == "rel":
            relative_disp = np.abs(coords) # Component-wise distance
        else:
            raise ValueError("Stage.move(): Movement mode should be 'abs' or 'rel'.")
        relative_dist = np.sqrt(relative_disp[0]**2 + relative_disp[1]**2) # Hypotenuse
        vx = velocity * relative_disp[0] / relative_dist
        vy = velocity * relative_disp[1] / relative_dist
        
        # Move the stage
        self.move_x(coords[0], length_units=length_units, velocity=vx, velocity_units=velocity_units, mode=mode, wait_until_idle=False)
        self.move_y(coords[1], length_units=length_units, velocity=vy, velocity_units=velocity_units, mode=mode, wait_until_idle=wait_until_idle)
        # To move x and y at the same time, start x moving first and then move y.
        # If y finishes before x, control will pass back out while x is still moving - this may result in undefined behaviour.
        # Make sure that if we want to wait until idle, both x and y have finished before passing control back out.
        if wait_until_idle:
            last = 0
            x_pos, y_pos = self.axis2.get_position(Units.LENGTH_MILLIMETRES), self.axis1.get_position(Units.LENGTH_MILLIMETRES)
            #TODO: Maybe do this using velocity?
            while abs(coords[0] - x_pos) > self.mm_resolution or abs(coords[1] - y_pos) > self.mm_resolution:
                if last == np.sqrt((coords[0] - x_pos)**2 + (coords[1] - y_pos)**2) and last < self.mm_resolution:
                    break
                x_pos, y_pos = self.axis2.get_position(Units.LENGTH_MILLIMETRES), self.axis1.get_position(Units.LENGTH_MILLIMETRES)
                last = np.sqrt((coords[0] - x_pos)**2 + (coords[1] - y_pos)**2)
                # Ease computation - only check if we are done 10 times per second.
                time.sleep(.1)
    
    def circle(self, centre, radius, N, T, length_units=Units.LENGTH_MILLIMETRES):
        """
        Trace out a circle with some radius from the centre. Done by modelling
        it as an N-sided polygon traced out in time T.
        """
        v0 = 2*np.pi*radius / T
        # Circumferential positions. x-component modelled as real data, y- as imag.
        # Round to 6 decimal places, as when close to zero this can have weird behaviour.
        circle_r = np.round(radius*np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1] * 1j, 6) + centre[0] + 1j*centre[1]
        
        vel_units = h.velocity_units(length_units)
        
        self.move(centre + np.squeeze([radius, 0]), length_units=length_units)
        for i in range(N):
            self.move([np.real(circle_r[i]), np.imag(circle_r[i])], length_units=length_units, velocity=v0, velocity_units=vel_units)


# def circle_polygonal(axis1, axis2, C, r, N, T, length_units=Units.LENGTH_MILLIMETRES):
#     """
#     Trace out a circle with two perpendicular axes. Approximates the circle
#     with an N-sided polygon. Currently has stop-start behaviour between each
#     segment.

#     Parameters
#     ----------
#     axis1 : TYPE
#         DESCRIPTION.
#     axis2 : TYPE
#         DESCRIPTION.
#     C : list, array
#         Centre position of the circle with units in dist_units.
#     r : float
#         Radius of the circle with units in dist_units.
#     N : int
#         Number of lines to discretise the circle into.
#     T : float
#         Desired total time taken in seconds. Note no checks made to ensure that
#         resulting velocity is physical - this is left to the user.
#     dist_units : Units, optional
#         Units of distance used. The default is Units.LENGTH_MILLIMETRES.
#     """
#     v0 = 2*np.pi*r / T
#     circle_r = np.round(r *np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1] * 1j, 6)
#     circle_v = np.round(v0*np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1], 6)
    
#     vel_units = h.velocity_units(length_units)
    
#     axis1.move_absolute(C[1], length_units)
#     axis2.move_absolute(C[0]+r, length_units)
#     for ii in range(N):
#         # If axis1 doesn't move
#         if np.abs(np.real(circle_v[ii])) == 0:
#             move_abs_v(axis2, C[0]+np.imag(circle_r[ii]), velocity=np.abs(np.imag(circle_v[ii])), velocity_units=vel_units)
#         # If axis2 doesn't move
#         elif np.abs(np.imag(circle_v[ii])) == 0:
#             move_abs_v(axis1, C[1]+np.real(circle_r[ii]), velocity=np.abs(np.real(circle_v[ii])), velocity_units=vel_units)
#         # Then both must move
#         else:
#             move_abs_v(axis1, C[1]+np.real(circle_r[ii]), velocity=np.abs(np.real(circle_v[ii])), velocity_units=vel_units, wait_until_idle=False)
#             move_abs_v(axis2, C[0]+np.imag(circle_r[ii]), velocity=np.abs(np.imag(circle_v[ii])), velocity_units=vel_units)
