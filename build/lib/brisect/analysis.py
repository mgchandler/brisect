# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 10:29:35 2023

@author: mc16535

A file containing functions which analyse output data acquired using the scan
module.
"""
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

def correct_liftoff(*args):
    """
    Corrects for the liftoff. Uses the linear fitting function to determine
    drift, and scales the data to the maximum value in data[:, 2].

    Parameters
    ----------
    data : ndarray (n, 3)
        Assumes that column 0 contains x-coordinates, column 1 contains y-
        coordinates and column 2 contains the data which is being fitted.

    Returns
    -------
    data : ndarray (n, 3)
        0th and 1st columns unchanged, 2nd column is corrected using the linear
        liftoff function.
    """
    if len(args) == 1:
        data = args[0]
    elif len(args) == 3:
        num_pts = []
        for arg in args:
            num_pts.append(arg.shape[0])
            # Check that data has the right dimensions
            if len(arg.shape) != 1:
                raise ValueError("correct_liftoff: Input data has the wrong shape.")
            # Check that all inputs have the same number of data points.
            if len(num_pts) != 0:
                for pt in num_pts:
                    if arg.shape[0] != pt:
                        raise ValueError("correct_liftoff: Number of points in input arrays should be the same.")
        data = np.array([args[0], args[1], args[2]]).T
    else:
        raise NotImplementedError("correct_liftoff: Wrong number of arguments provided.")
    
    params = lin_liftoff_params(data)
    
    # Do the correction.
    if params.shape[0] == 3:
        data[:, 2] = np.nanmax(data[:, 2]) * data[:, 2] / (params[0] * data[:, 0] + 
                                                           params[1] * data[:, 1] + 
                                                           params[2])
    elif params.shape[0] == 6:
        data[:, 2] = np.nanmax(data[:, 2]) * data[:, 2] / (params[0] * data[:, 0]**2 + 
                                                           params[1] * data[:, 0] * data[:, 1] +
                                                           params[2] * data[:, 1]**2 + 
                                                           params[3] * data[:, 0] +
                                                           params[4] * data[:, 1] +
                                                           params[5])
    
    if len(args) == 1:
        return data
    elif len(args) == 3:
        return np.squeeze(data[:, 0]), np.squeeze(data[:, 1]), np.squeeze(data[:, 2])

def lin_liftoff_params(data):
    """
    Fits a linear curve to data, returning coefficients A, B and C of the eqn
    z = Ax + By + C, where z are the measured values.

    Parameters
    ----------
    data : ndarray (n, 3)
        Assumes that column 0 contains x-coordinates, column 1 contains y-
        coordinates and column 2 contains the data which is being fitted.

    Returns
    -------
    A, B, C : floats
        Coefficients of the linear equation z = Ax + By + C.
    """
    threshold = (np.nanmax(data[:, 2]) - np.nanmin(data[:, 2])) / 1.5
    data = data[data[:, 2] > np.nanmin(data[:, 2])+threshold, :]
    A = np.vstack([data[:, 0], data[:, 1], np.ones(data.shape[0])]).T
    return np.linalg.lstsq(A, data[:, 2], rcond=None)[0]

def quad_liftoff_params(data):
    """
    Fits a linear curve to data, returning coefficients A, B and C of the eqn
    z = Ax^2 + Bxy + Cy^2 + Dx + Ey + F, where z are the measured values.

    Parameters
    ----------
    data : ndarray (n, 3)
        Assumes that column 0 contains x-coordinates, column 1 contains y-
        coordinates and column 2 contains the data which is being fitted.

    Returns
    -------
    A, B, C, D, E, F : floats
        Coefficients of the linear equation z = Ax^2 + Bxy + Cy^2 + Dx + Ey + F.
    """
    threshold = (np.nanmax(data[:, 2]) - np.nanmin(data[:, 2])) / 1.5
    data = data[data[:, 2] > np.nanmin(data[:, 2])+threshold, :]
    A = np.vstack([data[:, 0]**2, data[:, 0]*data[:, 1], data[:, 1]**2, data[:, 0], data[:, 1], np.ones(data.shape[0])]).T
    return np.linalg.lstsq(A, data[:, 2], rcond=None)[0]

def fit_geometry_to_data(*args, geom_profile="rect", init_params="default"):
    """
    Attempts to work out the geometry of the sample measured in "data" by using
    scipy's curve_fit function. Note that each geometry must have its own
    distance minimisation function defined.
    
    data is assumed to be an ndarray with shape (N, 3) containing N 
    measurements, where the 0th col contains the x-coords, the 1st col contains
    the y-coords and the 2nd col contains float data measured from the
    handyscope.
    
    init_params can be one of three forms:
        - None: 
            do not use any initial parameters.
        - "default":
            use the default initial parameters specified in the geometry dict.
        - list of params:
            specify the initial parameters to use.
            
    """
    if len(args) == 1:
        data = args[0]
    elif len(args) == 3:
        num_pts = []
        for arg in args:
            num_pts.append(arg.shape[0])
            # Check that data has the right dimensions
            if len(arg.shape) != 1:
                raise ValueError("correct_liftoff: Input data has the wrong shape.")
            # Check that all inputs have the same number of data points.
            if len(num_pts) != 0:
                for pt in num_pts:
                    if arg.shape[0] != pt:
                        raise ValueError("correct_liftoff: Number of points in input arrays should be the same.")
        data = np.array([args[0], args[1], args[2]]).T
    else:
        raise NotImplementedError("correct_liftoff: Wrong number of arguments provided.")
    
    geom_profile_dict = {
        "rect" : [lst_dist_from_rect, [80, 40, 50, 50, 0]],
    }
    if init_params == "default":
        init_params = geom_profile_dict[geom_profile][1] 
    
    # We expect the largest change in voltage to occur when the probe is moving
    # from off the sample to on the geometry. Differentiate the measurements
    # and filter based on that.
    grad = np.abs(np.diff(data[:, 2]) / np.linalg.norm([np.diff(data[:, 0]), np.diff(data[:, 1])]))
    #TODO: Need to choose a more appropriate threshold.
    grad_threshold = np.nanmax(grad)/10
    data = data[:-1, :]
    data = data[grad > grad_threshold, :]
    
    params, cov_mat = curve_fit(
        geom_profile_dict[geom_profile][0],
        data[:, :2].T,
        np.zeros(data.shape[0]),
        p0=init_params
    )
    return params

def dist_from_line(pt, start, end):
    """
    Calculates the distance of m points with coordinates "pt" from the line
    segment which starts at coordinates "start" and ends at "end". Note that as
    a segment is used rather than a line, this distance will not necessarily be
    the length of a vector normal to the line.

    Parameters
    ----------
    pt : ndarray (n, m)
        Coordinates of m points for which distance will be calculated.
        n-dimensional numpy array.
    start : ndarray (n,)
        Coordinates of one point on the line. n-dimensional numpy array.
    end : ndarray (n,)
        Coordinates of a second point on the line. n-dimensional numpy array.

    Returns
    -------
    dist : ndarray (m,)
        Distances of the points at coordinates "pt" from the line defined by
        points "start" and "end".
    """
    pt, start, end = np.asarray(pt, dtype=float), np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    # Check same dimension, check there is one start coord, check that start and end have same shape.
    if pt.shape[0] != start.shape[0] or start.shape != end.shape:
        raise ValueError("dist_from_line: Number of dimensions in coordinates are not consistent.")
    if len(start.shape) != 1:
        raise ValueError("dist_from_line: Too many coordinates defined for line.")
    if len(pt.shape) == 1:
        pt = pt.reshape((pt.shape[0], 1))
    # Get vectors from origin.
    v1 = end - start
    v2 = pt - start.reshape((-1, 1))
    # Get dot-product of vectors scaled wrt segment (i.e. |v1| -> 1, |v2| -> |v2|/|v1|).
    # This is the location of the nearest point on the line in % of segment length.
    nearest_perc = np.dot(v1/np.linalg.norm(v1), v2/np.linalg.norm(v1))
    # If nearest point is beyond the limits of the segment, set these to the limits so we find distance to segment.
    nearest_perc[nearest_perc < 0.] = 0.
    nearest_perc[nearest_perc > 1.] = 1.
    # Work out the distance between each point and its nearest point on the line.
    nearest = v1.reshape(-1, 1) * nearest_perc
    return np.linalg.norm(v2 - nearest, axis=0)

def lst_dist_from_rect(pt, origin_x, origin_y, width, height, rotation):
    """
    Calculates the distance of m points with coordinates "pt" from the nearest
    edge of a rectangle. The rectangle is defined with bottom-left corner
    "origin" with some "height" in the y-axis and "width" in the x-axis, and
    may have some "rotation" about "origin". Note that distance units are not
    required and so must be kept consistent by the user.

    Parameters
    ----------
    pt : ndarray (2, m)
        Coordinates of m points for which the distance from the nearest edge
        will be calcualted.
    origin : ndarray (2,)
        Coordinates of the bottom-left corner of the rectangle.
    height : float
        Height of the rectangle in the y-axis (before it is rotated).
    width : float
        Width of the rectangle in the x-axis (before it is rotated).
    rotation : float
        Rotation (radians) of the rectangle about "origin". +ve rotation
        defined conventionally as anti-clockwise.

    Returns
    -------
    dist : ndarray (m,)
        Distances of the points from the nearest edge in the rectangle.
    """
    pt, origin = np.asarray(pt, dtype=float), np.asarray([origin_x, origin_y], dtype=float)
    height, width, rotation = float(height), float(width), float(rotation)
    if pt.shape[0] != 2 or origin.shape[0] != 2:
        raise ValueError("least_dist_from_rect: Coordinates must be 2D.")
    if len(origin.shape) != 1:
        raise ValueError("least_dist_from_rect: Too many coordinates defined for origin.")
    # Initialise rotation matrix. Note that sign of sins is flipped as dims as origin is a row vector rather than a column vector.
    rotation_matrix = np.asarray([[np.cos(rotation), np.sin(rotation)], [-np.sin(rotation), np.cos(rotation)]])
    # Convert inputs to the four corners of the rectangle.
    corner1 = origin
    corner2 = origin + np.dot(np.asarray([width, 0]),      rotation_matrix)
    corner3 = origin + np.dot(np.asarray([width, height]), rotation_matrix)
    corner4 = origin + np.dot(np.asarray([0,     height]), rotation_matrix)
    # Calculate the distance to each of the four segments.
    dist1 = dist_from_line(pt, corner1, corner2)
    dist2 = dist_from_line(pt, corner2, corner3)
    dist3 = dist_from_line(pt, corner3, corner4)
    dist4 = dist_from_line(pt, corner4, corner1)
    # Get the smallest distance for each of the points.
    return np.min([dist1, dist2, dist3, dist4], axis=0)