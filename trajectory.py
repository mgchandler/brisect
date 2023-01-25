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

eps = 1e-4

class Stage:
    __slots__ = ("connection", "axis1", "axis2", "mm_resolution")
    
    def __init__(self, port=None, initial_position=None, length_units=Units.LENGTH_MILLIMETRES, mm_resolution=eps):
        if port is None:
            port = h.get_port()
        self.connection = Connection.open_serial_port(port)
        device_list = self.connection.detect_devices()
        
        self.axis1 = device_list[1].get_axis(1) # SN39116
        self.axis2 = device_list[0].get_axis(1) # SN39117
        
        if initial_position is not None:
            initial_position = np.squeeze(initial_position)
            if initial_position.shape != (2,):
                raise ValueError("Stage: initial_position should be a list of two coordinates")
            self.move_abs(initial_position, length_units=length_units)
        
        self.mm_resolution = eps
    
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
        
        Parameters
        ----------
        coords : ndarray (2,)
            Coordinates to move the stage to.
        length_units : Units, optional
            Units in which coordinates are defined. The default is
            Units.LENGTH_MILLIMETRES.
        velocity : float, optional
            Velocity at which the stage moves. No checks are made in this
            method on it being too large. The default is 10.
        velocity_units : Units, optional.
            Units of velocity. The default is 
            Units.VELOCITY_MILLIMETRES_PER_SECOND
        mode : string, optional.
            Method of movement. "abs" will move the stage to the exact
            coordinates provided; "rel" will move the stage relatively by the
            coordinates provided from the current position.
        wait_until_idle : bool, optional.
            Does the stage wait until the movement is complete before returning
            control to the user? Set to False if the handyscope is acquiring
            data at the same time.
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
    
    def circle(self, centre, radius: float, N: int, T: float, length_units=Units.LENGTH_MILLIMETRES):
        """
        Trace out a circle with some radius from the centre. Done by modelling
        it as an N-sided polygon traced out in time T.
        
        Parameters
        ----------
        centre : ndarray (2,)
            Coordinates of the centre of the circle.
        radius : float
            Radius of the circle.
        N : int
            Number of sides to use in the polygon when approximating the
            circle. larger N -> more circular.
        T : float
            Time in which to sweep out the circle (seconds). No checks are made
            on how this impacts velocity - if it's too small then the circle
            won't work properly.
        length_units : Units, optional
            Units used for all distances. The default is
            Units.LENGTH_MILLIMETRES
        """
        v0 = 2*np.pi*radius / T
        # Circumferential positions. x-component modelled as real data, y- as imag.
        # Round to 6 decimal places, as when close to zero this can have weird behaviour.
        circle_r = np.round(radius*np.exp(2j*np.pi*np.linspace(0, 1, N+1))[:-1] * 1j, 6) + centre[0] + 1j*centre[1]
        
        vel_units = h.velocity_units(length_units)
        
        self.move(centre + np.squeeze([radius, 0]), length_units=length_units)
        for i in range(N):
            self.move([np.real(circle_r[i]), np.imag(circle_r[i])], length_units=length_units, velocity=v0, velocity_units=vel_units)



def grid_sweep_coords(separation: float, x_init: float, y_init: float, width: float, height: float, rotation: float, eps=eps):
    """
    Generate coordinates of a grid sweep within a rectangle. Rectangle is
    defined by the bottom-left corner, its width, height and rotation about the
    origin, and the sweep has spacing defined by separation. Note that the 
    cells of the grid will all be square except for the edges if (width/sep) is
    not an integer.

    Parameters
    ----------
    separation : float
        Separation of rows/columns in the grid.
    x_init : float
        x-coordinate of the origin.
    y_init : float
        y-coordinate of the origin.
    width : float
        Width of the rectangle (i.e. length in x-axis before rotation).
    height : float
        Height of the rectangle (i.e. length in y-axis before rotation).
    rotation : float
        Rotation (radians) of the rectangle about the origin.
    eps : float, optional
        Error value used for checking equivalence. Used to determine if the row
        or column has exceeded the bounds. The default is eps.

    Returns
    -------
    coords : ndarray (N, 2)
        2D coordinates to be swept out. 
    """
    
    coords = np.zeros((0, 2))
    x, y = x_init, y_init
    
    #%% Snake up through y. Grid will form in the axes of the square. Separation
    # between rows will be equal to separation, length will span the full width.
    # Terminate on the row before we leave the limits of the geometry.
    idx = 0
    while y - (y_init + height * np.cos(rotation)) < eps:
        coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # Move from left -> right
        if idx%2 == 0:
            x += width * np.cos(rotation)
            y += width * np.sin(rotation)
        # Move from right -> left
        else:
            x -= width * np.cos(rotation)
            y -= width * np.sin(rotation)
        coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # Move up to the next row
        x += separation * np.sin(rotation)
        y += separation * np.cos(rotation)
        
        idx += 1
        
    # We are currently outside of the geometry. To scan the full span, do a final
    # row at the limit.
    if idx%2 == 0:
        coeff = +1
        # Top left
        x = x_init + height * np.sin(rotation)
        y = y_init + height * np.cos(rotation)
        coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # Move left -> right
        x += width * np.cos(rotation)
        y += width * np.sin(rotation)
    else:
        coeff = -1
        # Top right
        x = x_init + width * np.cos(rotation) + height * np.sin(rotation)
        y = y_init + width * np.sin(rotation) + height * np.cos(rotation)
        coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # Move right -> left
        x -= width * np.cos(rotation)
        y -= width * np.sin(rotation)
    
    #%% Snake back through x. x may be increasing or decreasing depending on
    # where y terminated - check both lower and upper limits of x.
    idx = 0
    while x - (x_init - height * np.sin(rotation)) >= eps and x - (x_init + height * np.sin(rotation) + width * np.cos(rotation)) <= eps:
        coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # Move top -> bottom
        if idx%2 == 0:
            x -= height * np.sin(rotation)
            y -= height * np.cos(rotation)
        # Move bottom -> top
        else:
            x += height * np.sin(rotation)
            y += height * np.cos(rotation)
        coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # Move along to next column
        x -= coeff * separation * np.cos(rotation)
        y -= coeff * separation * np.sin(rotation)
        
        idx += 1
        
    # Do the final column at the limit.
    # If x is increasing with subsequent columns
    if coeff == -1:
        # If we terminated at the top
        if idx%2 == 0:
            x = x_init + width * np.cos(rotation) + height * np.sin(rotation)
            y = y_init + width * np.sin(rotation) + height * np.cos(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
            # Move top -> bottom
            x -= height * np.sin(rotation)
            y -= height * np.cos(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # If we terminated at the bottom
        else:
            x = x_init + width * np.cos(rotation)
            y = y_init + width * np.sin(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
            # Move bottom -> top
            x += height * np.sin(rotation)
            y += height * np.cos(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
    # If x is decreasing with subsequent columns
    else:
        # If we terminated at the top
        if idx%2 == 0:
            x = x_init + height * np.sin(rotation)
            y = y_init + height * np.cos(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
            # Move top -> bottom
            x -= height * np.sin(rotation)
            y -= height * np.cos(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
        # If we terminated at the bottom
        else:
            x = x_init
            y = y_init
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
            # Move bottom -> top
            x += height * np.sin(rotation)
            y += height * np.cos(rotation)
            coords = np.append(coords, np.reshape([x, y], (1, 2)), axis=0)
    
    return coords