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
    __slots__ = ("connection", "axes", "mm_resolution")
    
    def __init__(self,
            port: str = None, 
            initial_position: list[float] = None,
            length_units: Units.LENGTH_XXX = Units.LENGTH_MILLIMETRES,
            mm_resolution: float = eps
        ):
        if port is None:
            port = h.get_port()
        self.connection = Connection.open_serial_port(port)
        device_list = self.connection.detect_devices()
        
        self.axes = []
        for device in device_list:
            self.axes.append(device.get_axis(1))
        # Note that this has the order of the devices. It may be convenient to
        # assume that these go as x, y, z, etc - if this is not the case, change
        # the order of the axes using the Zaber console.
        
        if initial_position is not None:
            initial_position = np.squeeze(initial_position)
            if initial_position.shape != (2,):
                raise ValueError("Stage: initial_position should be a list of two coordinates")
            self.move_abs(initial_position, length_units=length_units)
        
        self.mm_resolution = eps
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Reset velocity for Qiuji
        for axis in self.axes:
            axis.settings.set("maxspeed", 15, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        self.connection.close()
    
    def __str__(self):
        s  = "Zaber motion stage\n"
        for idx, axis in enumerate(self.axes):
            s += f"\tAxis{idx+1}:\n"
            s += "\t\tPosition: {:9.6f}mm\n".format(axis.get_position())
        return s
    
    def shutdown(self):
        # Reset velocity for Qiuji
        for axis in self.axes:
            axis.settings.set("maxspeed", 15, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        self.connection.close()  
    
    def stop(self):
        """
        Terminates movement of the axes.
        """
        for axis in self.axes:
            axis.stop()
    
    def move(self,
            coords: np.ndarray,
            length_units: Units.LENGTH_XXX = Units.LENGTH_MILLIMETRES,
            velocity: float = 10,
            velocity_units: Units.VELOCITY_XXX = Units.VELOCITY_MILLIMETRES_PER_SECOND,
            mode: str = "abs",
            wait_until_idle: bool = True
        ):
        """
        Move the stage to a set of coordinates (x, y, ...) - these can either
        be in the absolute axis coordinates, or relative to the current
        position. Velocity is taken to mean the total velocity that the stage
        moves in the each direction, i.e. velocity=sqrt(v_x^2 + v_y^2 + ...)
        
        Parameters
        ----------
        coords : ndarray (N,)
            Coordinates to move the stage to. You can only supply coordinates
            up to the number of axes. Any axes after that will not move. No
            checks are made on the order of axes, use Zaber console to reorder
            axes.
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
        if len(coords.shape) != 1 or coords.shape[0] > len(self.axes):
            raise TypeError("Stage.move(): coordinates must be supplied as a list of floats. Make sure the list is 1D and there are fewer than the number of axes available.")
        
        # Convert velocity into displacement units.
        if velocity_units != h.velocity_units(length_units):
            native_value = self.axes[0].settings.convert_to_native_units("vel", velocity, velocity_units)
            velocity = self.axes[0].settings.convert_from_native_units("vel", native_value, h.velocity_units(length_units))
            velocity_units = h.velocity_units(length_units)
        
        # Compute components of velocity in each direction.
        if mode == "abs":
            old_coords = np.asarray([axis.get_position(length_units) for axis in self.axes])
            relative_displacement = np.abs(coords - old_coords[:len(coords)]) # Component-wise distance
        elif mode == "rel":
            relative_displacement = np.abs(coords) # Component-wise distance
        else:
            raise ValueError("Stage.move(): Movement mode should be 'abs' or 'rel'.")
            
        relative_distance = np.sqrt(np.sum(relative_displacement**2)) # Hypotenuse
        vels = velocity * relative_displacement / relative_distance
        # For each axis in this movement, we do not want to wait until idle unless we are on the very last axis.
        idle_list = [False] * coords.shape[0]
        idle_list[-1] = wait_until_idle
        
        # Move the stage
        for idx, [r, v] in enumerate(zip(coords, vels)):
            self.axes[idx].settings.set("maxspeed", v, velocity_units)
            if mode == "abs":
                self.axes[idx].move_absolute(r, length_units, wait_until_idle=idle_list[idx])
            elif mode == "rel":
                self.axes[idx].move_relative(r, length_units, wait_until_idle=idle_list[idx])
            else:
                raise ValueError("Movement mode should be 'abs' or 'rel'.")
        
        # Move x, y and maybe z at the same time, but issue commands in that order.
        # Control returns when the last one finishes - if y finishes before x, control is returned
        # before this method has terminated. We want to avoid this.
        if wait_until_idle:
            # While any axes are still busy
            while any([self.axes[i].is_busy() for i in range(len(self.axes))]):
                # Sleep and try again in .1 seconds
                time.sleep(.1)
    
    def circle(self,
            centre: list[float],
            radius: float,
            N: int,
            T: float, 
            length_units: Units.LENGTH_XXX = Units.LENGTH_MILLIMETRES,
        ):
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



def grid_sweep_coords(
        separation: float,
        x_init: float,
        y_init: float,
        width: float,
        height: float,
        rotation: float,
        eps: float = eps,
    ) -> np.ndarray[float]:
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