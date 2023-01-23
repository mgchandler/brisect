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

def fit_geometry_to_data(data, geom_profile="rect", init_params="default"):
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
    data_grad = data[grad > grad_threshold, :]
    
    data_fit = data[data[:, 2] > .8, :]
    A = np.vstack([data_fit[:, 0], data_fit[:, 1], np.ones(data_fit.shape[0])]).T
    a, b, c = np.linalg.lstsq(A, data_fit[:, 2], rcond=None)[0]
    
    data_corrected = data_fit
    data_corrected[:, 2] = data_corrected[:, 2] / (a*data_fit[:, 0] + b*data_fit[:, 1] + c)
    
    params, cov_mat = curve_fit(
        geom_profile_dict[geom_profile][0],
        data_grad[:, :2].T,
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

def lst_dist_from_rect(pt, origin_x, origin_y, height, width, rotation):
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



if __name__ == "__main__":
    filename = r".\output\CoarseScanSingleFreq.csv"
    data = np.loadtxt(filename, skiprows=1, delimiter=',')
    params = fit_geometry_to_data(data)
    
    rotation_matrix = np.asarray([[np.cos(params[4]), np.sin(params[4])], [-np.sin(params[4]), np.cos(params[4])]])
    corner1 = [params[0], params[1]]
    corner2 = [params[0], params[1]] + np.dot(np.asarray([params[3], 0]),         rotation_matrix)
    corner3 = [params[0], params[1]] + np.dot(np.asarray([params[3], params[2]]), rotation_matrix)
    corner4 = [params[0], params[1]] + np.dot(np.asarray([0,         params[2]]), rotation_matrix)
    
    plt.plot([corner1[0], corner2[0], corner3[0], corner4[0], corner1[0]], [corner1[1], corner2[1], corner3[1], corner4[1], corner1[1]], 'r')
    plt.scatter(data[:, 0], data[:, 1], c=data[:, 2], marker='.')
    plt.colorbar(label="RMS Voltage (V)")
    plt.gca().set_aspect('equal')
    plt.show()