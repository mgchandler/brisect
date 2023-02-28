# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 14:37:59 2023

@author: mc16535

Demonstration of a chirp signal scan.
"""
# from brisect.handyscope import Handyscope
import matplotlib.pyplot as plt
import numpy as np
import os
os.chdir(r"C:\Users\mc16535\OneDrive - University of Bristol\Documents\Postgrad\Coding\brisect\examples\chirp_ex")

freq_1 = 0.2e3
freq_2 = 55e3

# See yaml file saved externally.
with Handyscope.from_yaml("chirp_ex.yml") as scope:
    # Work out the input signal
    timepts = np.linspace(0, (scope.scp.record_length-1)/scope.gen.frequency, scope.scp.record_length)
    signal = np.sin(2*np.pi*timepts * (freq_1 + timepts * (freq_2 - freq_1)/(2*timepts[-1])))
    scope.set_data(signal)
    
    # Do the data collection.
    data = scope.get_record()
    
    # Do some processing
    plt.plot(data[0, :])
plt.show()