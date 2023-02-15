# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 15:34:27 2022

@author: mc16535

A file containing functions which combine the zaber stage and the handyscope.
"""
import handyscope as hs
import helpers as h
import matplotlib.pyplot as plt
import numpy as np
import time
import trajectory as traj
from typing import Callable, Optional, Tuple
import warnings
from zaber_motion import Units

def geometry_search(
        handyscope: hs.Handyscope, 
        stage: traj.Stage,
        origin: np.ndarray[float] = [0.,0.,0.],
        width: float = 200.,
        height: float = 200.,
        rotation: float = 0.,
        snake_separation: float = 50.,
        fuzzy_separation: float = 1.,
        length_units: Units.LENGTH_XXX = Units.LENGTH_MILLIMETRES,
        velocity: float = 5.,
        velocity_units: Units.VELOCITY_XXX = Units.VELOCITY_MILLIMETRES_PER_SECOND,
        live_plot: bool = False
    ):
    """
    Search within the domain for the geometry. Invokes a snake-like pattern to
    find the geometry in the first instance. When a change in RMS voltage is
    detected which is believed to be due to passing onto the geometry, a snake-
    like search is performed to trace the outline of the geometry (called fuzzy
    sweep).
    
    N.B. This function will replace grid_sweep_scan().

    Parameters
    ----------
    handyscope : Handyscope obj
        Handyscope object from module `handyscope`. Should already have been
        initialised.
    stage : Stage obj
        Stage object from module `trajectory`. Should already have been
        initialised.
    origin : ndarray (N,), optional
        Coordinates of the origin of the grid. Size N should be <= the number
        of axes in stage. The sweep will be performed over the first two
        axes. The default is [0,0,0].
    width : float, optional
        Width of the grid in the 0th axis (i.e. before rotation) in
        length_units. The default is 200.
    height : float, optional
        Height of the grid in the 1st axis (i.e. before rotation) in
        length_units. The default is 200.
    rotation : float, optional
        Rotation of the grid about the origin in radians. The default is 0.
    snake_separation : float, optional
        Distance which separates rows and columns of the grid in length_units.
        The default is 50.
    fuzzy_separation : float, optional
        Distance which separates each pass in the fuzzy scan in length_units.
        The default is 1.
    length_units : Length_Units, optional
        Units in which all distances are provided, imported from 
        zaber_motion.Units. The default is Units.LENGTH_MILLIMETRES.
    velocity : float, optional
        Speed at which to perform the snake scan in velocity_units. The default 
        is 5.
    velocity_units : Velocity_Units, optional
        Units in which velocity is provided, imported from zaber_motion.Units.
        The default is Units.VELOCITY_MILLIMETRES_PER_SECOND.
    live_plot : bool, optional
        Setting of whether to plot the . The default is False.
    """
    # Input checking
    if len(stage.axes) < 2:
        raise ValueError("scan.geometry_search: not enough axes to perform 2D sweep search for geometry.")
    origin = np.squeeze(origin)
    if len(origin.shape) != 1 or origin.shape[0] > len(stage.axes):
        raise ValueError("scan.geometry_search: origin must be array-like coordinates of length <= axes in stage.")
    #TODO: check that handyscope is recording RMS voltage
    # Determine coordinates of the grid
    coords = traj.grid_sweep_coords(snake_separation, origin[0], origin[1], width, height, rotation)
    # Initialise stage position
    stage.move(coords, length_units=length_units, velocity=velocity, velocity_units=velocity_units)
    # Define break function: occurs when we move from off-geometry (low RMS) to on-geometry (high RMS). Assume that on geometry is >1% larger.
    off_geom = h.rms(handyscope.get_record())
    find_geometry = lambda rms: rms > 1.01*off_geom
    
    #%% Start the scan.
    rms_data = None
    for idx, step in enumerate(coords):
        # Do the actual scan
        if live_plot:
            coordinates, rms_scan, break_state = linear_scan(
                handyscope,
                stage,
                step,
                length_units=length_units,
                velocity=velocity,
                velocity_units=velocity_units,
                break_fn=find_geometry,
                live_plot=True,
                old_val=rms_data
            )
        else:
            coordinates, rms_scan, break_state = linear_scan(
                handyscope,
                stage,
                step,
                length_units=length_units,
                velocity=velocity,
                velocity_units=velocity_units,
                break_fn=find_geometry
            )
        
        # If we have found the geometry
        if break_state:
            warnings.warn("Geometry tracing not yet implemented. Geometry found, continuing search.")
            print("geometry found!")
            stage.move(step, length_units=length_units, velocity=velocity, velocity_units=velocity_units)
    
    # return x_data, y_data, rms_data

#%%
def trace_geometry(
        handyscope: hs.Handyscope,
        stage: traj.Stage,
        init_direction: np.ndarray[float],
        separation: float = 1.,
        length_units: Units.LENGTH_XXX = Units.LENGTH_MILLIMETRES,
        velocity: float = 1.,
        velocity_units: Units.VELOCITY_XXX = Units.VELOCITY_MILLIMETRES_PER_SECOND,
        live_plot: bool = False,
    ):
    """
    Traces the perimeter of the geometry which has just been found. The probe
    will move back and forth over the edge of the geometry, expecting to detect
    an increase and decrease in RMS voltage as it does so, to trace out the
    edge of the sample in one direction. When the probe reaches a corner, it is
    expected that the probe will be unable to detect an increase or decrease in
    RMS.

    Parameters
    ----------
    handyscope : Handyscope obj
        Handyscope object from module `handyscope`. Should already have been
        initialised.
    stage : Stage obj
        Stage object from module `trajectory`. Should already have been
        initialised.
    init_direction : np.ndarray[float]
        Direction in which the stage was travelling when the edge of the
        geometry was just found. By convention, the trace scan will start
        scanning to the right of this initial direction.
    separation : float, optional
        Separation between each pass over the edge of the geometry. The default
        is 1.
    length_units : Units.LENGTH_XXX, optional
        Units in which all distances are provided. The default is
        Units.LENGTH_MILLIMETRES.
    velocity : float, optional
        Velocity at which to perform the scan. This should be slower than the
        value which would be used in geometry_search(). The default is 1.
    velocity_units : Units.VELOCITY_XXX, optional
        Units in which velocity is provided. The default is
        Units.VELOCITY_MILLIMETRES_PER_SECOND.
    live_plot : bool, optional
        Whether to plot each point which is detected in the geometry. The
        default is False.
    """
    # Record the start position. Used to check whether we have completed tracing and terminate the loop.
    origin = stage.get_position(length_units)
    # Initialise start direction. Make it a unit vector of size == len(stage.axes)
    init_direction = np.squeeze(init_direction).reshape((-1, 1))
    if init_direction.shape[0] > len(stage.axes):
        raise ValueError("scan.trace_geometry: init_direction should be a vector of coodinates with length <= the number of axes.")
    if len(stage.axes) < 2:
        raise ValueError("scan.trace_geometry: geometry tracing requires at least two axes.")
    if init_direction.shape[0] != len(stage.axes):
        init_direction = np.append(init_direction, np.zeros((len(stage.axes)-init_direction.shape[0], 1)), axis=0)
    init_direction /= np.linalg.norm(init_direction)
    # Define rotation matrices for changing cardinal directions later.
    cwise = np.identity(len(stage.axes))
    ccwise = np.identity(len(stage.axes))
    cwise[:2, :2] = [[0, -1], [1, 0]]
    ccwise[:2, :2] = [[0, 1], [-1, 0]]
    # Define break functions for moving on the geometry and off the geometry.
    # Use geometry RMS and vacuum RMS to do this.
    stage.move(5*separation*init_direction, length_units=length_units, velocity=velocity, velocity_units=velocity_units, mode="rel", wait_until_idle=True)
    geom_rms = h.rms(handyscope.get_record())
    stage.move(-10*separation*init_direction, length_units=length_units, velocity=velocity, velocity_units=velocity_units, mode="rel", wait_until_idle=True)
    vac_rms = h.rms(handyscope.get_record())
    on_geometry = lambda rms: rms > (geom_rms + vac_rms)/2
    off_geometry = lambda rms: rms < (geom_rms + vac_rms)/2
    # Reset initial position.
    stage.move(origin, length_units=length_units, velocity=velocity, velocity_units=velocity_units, mode="abs", wait_until_idle=True)
    # Define initial cardinal direction.
    cardinal = np.dot(cwise, init_direction)
    
    #TODO: Check whether we need to move the start position into the geometry a little bit.
    
    first = True
    current_pos = stage.get_position(length_units)
    # We have just found the geometry, meaning that we are sat on top of it.
    while first or h.within_radius(origin, current_pos, separation):
        # Step once and move off the geometry.
        stage.move(separation*cardinal, length_units=length_units, velocity=velocity, velocity_units=velocity_units, mode="rel", wait_until_idle=True)
        coordinates, scan_data, break_state = linear_scan(
            handyscope,
            stage,
            3*separation*np.dot(cardinal, cwise),
            length_units=length_units,
            velocity=velocity,
            velocity_units=velocity_units,
            move_mode="rel",
            break_fn=off_geometry
        )
        current_pos = stage.get_position(length_units)
        
        # Step once and move on the geometry.
        stage.move(separation*cardinal, length_units=length_units, velocity=velocity, velocity_units=velocity_units, mode="rel", wait_until_idle=True)
        coordinates, scan_data, break_state = linear_scan(
            handyscope,
            stage,
            3*separation*np.dot(cardinal, ccwise),
            length_units=length_units,
            velocity=velocity,
            velocity_units=velocity_units,
            move_mode="rel",
            break_fn=on_geometry
        )
        current_pos = stage.get_position(length_units)


    
    
    
    
#%%
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

#%%
def linear_scan(
        handyscope: hs.Handyscope,
        stage: traj.Stage,
        target: np.ndarray[float],
        length_units: Units.LENGTH_XXX = Units.LENGTH_MILLIMETRES,
        velocity: float = 1.,
        velocity_units: Units.VELOCITY_XXX = Units.VELOCITY_MILLIMETRES_PER_SECOND,
        move_mode: str = "abs",
        scan_mode: str = "RMS",
        break_fn: Callable[[float], bool] = None,
        live_plot: bool = False,
        old_val: np.ndarray[float] = None
    ) -> Tuple[np.ndarray[float], np.ndarray[Optional[float, complex]], bool]:
    """
    Scans the sample using the handyscope while the stage moves the substrate
    in a line. Currently supports scanning RMS voltage and frequency spectrum
    data. Breaking out of the scan is also supported if a condition is met.
    
    N.B. This function will replace linear_scan_rms() and linear_scan_spec().

    Parameters
    ----------
    handyscope : Handyscope obj
        Handyscope object from module `handyscope`. Should already have been
        initialised.
    stage : Stage obj
        Stage object from module `trajectory`. Should already have been
        initialised.
    target : ndarray (N,)
        Coordinates of the position to move to, either in absolute coordinates
        or coordinates relative to the current position.
    length_units : Units.LENGTH_XXX, optional
        Units in which distances are provided. The default is
        Units.LENGTH_MILLIMETRES.
    velocity : float, optional
        Speed at which to move the stage. The default is 1.
    velocity_units : Units.VELOCITY_XXX, optional
        Units in which velocity is provided. The default is
        Units.VELOCITY_MILLIMETRES_PER_SECOND.
    move_mode : str, optional
        Mode of movement, either absolute ("abs") or relative ("rel"). The
        default is "abs".
    scan_mode : str, optional
        Mode of scanning, either RMS voltage ("RMS") or frequency spectrum
        ("spec"). The default is "RMS".
    break_fn : function(float)->bool, optional
        Condition on which to break out of the scan. Intended use is to provide
        a function which will return True when the most recently scanned value
        exceeds a threshold. This allows any type of check (<, >, ==, etc). The
        default is None, meaning that the scan will never break.
    live_plot : bool, optional
        Whether to plot the scan live as data is acquired. The default is 
        False.
    old_val : np.ndarray[float], optional
        Used when live_plot is True, new values are appended to the end of this
        array. The default is None, meaning that no values appended.

    Returns
    -------
    coordinates : ndarray (N, M)
        Coordinates of the stage when the mth scan was taken. Positions of all
        N axes are recorded.
    scan_data : ndarray (M,)
        Data acquired by the handyscope during the scan.
    break_state : bool
        Whether the stage terminated by reaching the target, or whether the
        break_fn returned True and the scan terminated early.
    """
    # Check inputs
    target = np.squeeze(target)
    if len(target.shape) != 1 or target.shape[0] > len(stage.axes):
        raise ValueError("scan.linear_scan: target must be array-like coordinates of length <= number of axes in stage.")
    valid_scans = ("rms", "spec")
    scan_mode = scan_mode.lower()
    if scan_mode not in valid_scans:
        raise ValueError("scan.linear_scan: scan mode must be one of {}".format(valid_scans))
        
    # Initialise output arrays
    coordinates = np.zeros((len(stage.axes), 0))
    if scan_mode == "rms":
        scan_data = np.zeros((0))
    elif scan_mode == "spec":
        freq = np.fft.rfftfreq(handyscope.scp.record_length, 1/handyscope.scp.sample_frequency)
        scan_data = np.zeros((freq.shape[0], 0))
    # Return state for break
    break_state = False
    
    # Start moving the stage
    stage.move(target, length_units=length_units, velocity=velocity, velocity_units=velocity_units, mode=move_mode, wait_until_idle=False)
    
    #%% Start collecting the data
    while any([stage.axes[i].is_busy() for i in range(len(stage.axes))]):
        step_loc = stage.get_position(length_units)
        scan_val = handyscope.get_record()
        
        # Process the data and store it
        coordinates = np.append(coordinates, step_loc, axis=1)
        if scan_mode == "rms":
            scan_data = np.append(scan_data, h.rms(scan_val))
        elif scan_mode == "spec":
            scan_data = np.append(scan_data, np.fft.rfft(scan_val[0, :]), axis=1)
        
        # Live plot it
        if live_plot:
            fig = plt.figure(figsize=(12,5),dpi=100)
            ax1 = fig.add_subplot(111)
            if scan_mode == "rms":
                if old_val is not None:
                    plt.plot(list(old_val[-100+len(scan_val):]) + scan_val)
                else:
                    plt.plot(scan_val)
            elif scan_mode == "spec":
                ax1.plot(freq*1e-6, np.abs(scan_val[-1]))
            plt.show(block=False)
        
        # Check whether to break
        if break_fn is not None:
            if break_fn(scan_val):
                stage.stop()
                break_state = True
                break
        
        # Sleep and try again in .1 seconds
        if not live_plot:
            time.sleep(.01)
    
    return coordinates, scan_data, break_state

#%%
def linear_scan_rms(handyscope, stage, target, length_units=Units.LENGTH_MILLIMETRES, velocity=1, velocity_units=Units.VELOCITY_MILLIMETRES_PER_SECOND, move_mode="abs", live_plot=False, old_val=None):
    """ 
    Collect RMS data from handyscope while stage moves the substrate in a line.
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