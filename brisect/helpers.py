# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 15:30:00 2022

@author: mc16535

A file containing helper functions for ect-smart-scan, which do not belong in
any other file. Should consist of short, easily read functions, rather than
anything too much more extensive.
"""
import csv
from importlib.resources import files
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import os
from serial.tools.list_ports import comports
from typing import Union
import yaml

#%% Connection functions.
def get_port(manufacturer: str = "FTDI"):
    """
    Returns the port which the device of interest is connected to. Serial does
    not guarantee that comports() returns ports in order, thus we sort by port.
    It is assumed that only one connection is available, thus the first one is
    returned; if none available then RuntimeError raised.
    """
    ports = sorted(comports(), key=lambda port: port.device)
    for port in ports:
        if port.manufacturer == manufacturer:
            return port.device
    raise RuntimeError("Device cannot be found! Connect it and make sure drivers are installed.")
    
#%% Input/output functions.
def read_settings(filename: str):
    """
    Reads in settings from file, and assigns default values when not given.
    """
    # Redefine default_settings here in case it has been overwritten in the
    # past.
    default_settings = {
        "job":{
            # Loose requirement: name of scan, used for saving.
            "name":"TestScan",
        },
        "material":{
            # Loose requirement: not used at the moment.
            "name":"Aluminium",
        },
        # All generator parameters are required.
        "generator":{
            # Optional: number of repeats of input signal. Only required for HS5.
            "burst_count": 1
        },
        "oscilloscope":{
            # Loose requirement: method of data acquisition.
            "mode":"MM_BLOCK",
            # Optional: bit-resolution of the oscilloscope.
            "resolution":12,
            # Optional: channels on which measurements are taken.
            "active_channels":[-1],
            # Optional: kind of data to be captured on all channels.
            "coupling":"CK_ACV",
        },
        "trajectory":{
            # Optional: initial position of the x-axis. Set to the middle.
            "init_x":100,
            # Optional: initial position of the y-axis. Set to the middle.
            "init_y":0,
        },
    }
    try:
        with open(filename, 'r') as file:
            settings = yaml.safe_load(file)
    except FileNotFoundError:
        file_path = files('brisect.default_settings').joinpath(filename)
        settings = yaml.safe_load(file_path.read_text())
    dict_merge(default_settings, settings)
    # default_settings now contains all the default values, plus everything
    # which has been overwritten by settings.
    return default_settings
    
def dict_merge(dict1: dict, dict2: dict):
    """
    Merge two dictionaries preserving sub-dictionaries contained within. Values
    from dict2 are merged into dict1, taking dict2's value over dict1's in
    conflicts.
    """
    for k, v in dict2.items():
        # Typical dictionary-merging behaviour is to overwrite the values in
        # dict1 with those in dict2. If the value is a dictionary, the entire
        # thing is overwritten rather than just duplicate terms. To preserve
        # values in dict1[k] which are not present in dict2[k], recursively
        # call dict_merge when we find a dictionary.
        if (k in dict1 and isinstance(dict1[k], dict) and isinstance(dict2[k], dict)):
            dict_merge(dict1[k], dict2[k])
        # Either we do not have a dictionary, or this item is not a dictionary
        # in dict1, thus we want to overwrite it anyway.
        else:
            dict1[k] = dict2[k]

def save_csv(
        filename: str,
        x: np.ndarray[float],
        y: np.ndarray[float],
        z: np.ndarray[Union[float, complex]],
        xunits: str = "mm",
        yunits: str = "mm",
        zlabel: str = "RMS Voltage (V)",
        zaxis: np.ndarray[float] = None,
        ignore_long_z_warning: bool = False
    ):
    """
    Saves a csv of data.
    """
    x, y, z = np.squeeze(x), np.squeeze(y), np.squeeze(z).reshape(z.shape[0], -1)
    zlabel = np.asarray(zlabel)
    # Only check 0th dim of z as it may be 2D.
    if x.shape != y.shape and y.shape[0] != z.shape[0]:
        raise ValueError("x, y and z should all have broadcastable shapes.")
    
    if z.shape[1] != 1:
        if z.shape[1] != zaxis.shape[0]:
            raise ValueError("1st dim of z and zaxis must have the same shape.")
        if z.shape[1] > 10 and not ignore_long_z_warning:
            raise ValueError("zaxis is too large. If you meant to save more than 10, set ignore_long_z_warning=True")
        zlabel = np.char.add(zlabel, zaxis.astype(str))
        
    # Check if the file already exists.
    if os.path.isfile(f"{filename}.csv"):
        idx = 1
        while os.path.isfile(f"{filename} ({idx}).csv"):
            idx += 1
        filename += f" ({idx})"
    
    print(f"Saving {filename}.csv ...")
    with open(f"{filename}.csv", 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([f"x ({xunits})", f"y ({yunits})"] + ["{}".format(label) for label in zlabel])
        for idx in range(x.shape[0]):
            csvwriter.writerow([x[idx], y[idx]] + list(z[idx, :]))
            
def plot_data(
        filename: str,
        x: np.ndarray[float],
        y: np.ndarray[float],
        z: np.ndarray[Union[float, complex]],
        xunits: str = "mm",
        yunits: str = "mm",
        zlabel: str = "RMS Voltage (V)"
    ):
    """
    Saves a single figure.
    """
    x, y, z = np.squeeze(x), np.squeeze(y), np.squeeze(z)
    zlabel = np.asarray(zlabel)
    # z must have the same shape - call plot_data() multiple times if multiple z's required.
    if x.shape != y.shape and y.shape != z.shape:
        raise ValueError("x, y and z should all have broadcastable shapes.")
        
    # Check if the file already exists.
    if os.path.isfile(f"{filename}.png"):
        idx = 1
        while os.path.isfile(f"{filename} ({idx}).png"):
            idx += 1
        filename += f" ({idx})"
    
    # For plotting, if complex do absolute
    if z.dtype == complex:
        z = np.abs(z)
    fig = plt.figure(figsize=(8,6), dpi=100)
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.8], projection='3d')
    graph = ax.scatter(x, y, z, c=z)
    ax.set_xlabel(f"x ({xunits})")
    ax.set_ylabel(f"y ({yunits})")
    ax.set_zlabel(zlabel)
    ax2 = fig.add_subplot(111)
    ax2.set_axis_off()
    fig.colorbar(graph, ax=ax2, label=zlabel)
    plt.savefig(f"{filename}.png")

#%% Useful data analysis functions.
def rms(x: np.ndarray[float]):
    """
    Compute the root-mean-square of a numpy vector.
    """
    return np.sqrt(np.mean(np.asarray(x)**2))

def within_radius(
        origin: np.ndarray[float],
        coords: np.ndarray[float],
        radius: float
    ) -> Union[bool, np.ndarray[bool]]:
    """ 
    Checks whether coordinates are within a radius of the origin, returning a
    boolean of the result of the test.
    """
    origin = np.squeeze(origin)
    if len(origin.shape) != 1:
        raise ValueError("within_radius: origin should be a 1D vector.")
    origin = origin.reshape(-1, 1)
    coords = np.squeeze(coords)
    if coords.shape[0] != origin.shape[0]:
        raise ValueError("within_radius: coords and origin should have the same number of dimensions.")
    if len(coords.shape) == 1:
        coords = coords.reshape(-1, 1)
    elif len(coords.shape) > 2:
        raise ValueError("within_radius: coords has the wrong shape.")
        
    distance = np.linalg.norm(coords - origin, axis=0)
    if len(distance) == 1:
        distance = distance[0]
    return distance < radius

def grid_sweep_coords(
        separation: float,
        x_init: float,
        y_init: float,
        width: float,
        height: float,
        rotation: float,
        eps: float = 1e-4,
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