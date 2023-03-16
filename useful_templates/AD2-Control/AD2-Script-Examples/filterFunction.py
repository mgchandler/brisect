"""
Function to perform the SNR measurement of the signal
"""

__author__ = "Richard Gold, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort Design Ltd., July 2022"
__version__ = "0.1.0"

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.signal import freqz

# =============================================================================
# def butter_bandpass(lowcut, highcut, fs, order):
#     return butter(order, [lowcut, highcut], fs=fs, btype='band')
# =============================================================================

def butter_bandpass_filter(data, order, lowcut, highcut, fs, btype):
    b, a = butter(order, [lowcut, highcut], fs, btype = 'band')
    # b, a = butter_bandpass(lowcut, highcut, fs, order = order)
    filtered_signal = filtfilt(b, a, data)
    return filtered_signal

def applyFilter(fs, y_data):
    lowcut = 1e6
    highcut = 5e6
    test_filt = butter_bandpass_filter(y_data, lowcut, highcut, fs, order = 5)
    
    return test_filt


##Use function below for visualising the filter response.
plotResponse = 1
lowcut = 2.5e6      #Hz
highcut = 7.5e6     #Hz
fs = 100e6        #Hz

if(plotResponse == 1):
    plt.figure(1)
    plt.clf()
    for order in [5]:
        b, a = butter(order, [lowcut, highcut], fs, btype='band')
        w, h = freqz(b, a, worN = 2000)
        plt.plot((fs * 0.5 / np.pi) * w, abs(h), label="order = %d" % order)

    plt.plot([0, 0.5 * fs], [np.sqrt(0.5), np.sqrt(0.5)], '--', label = 'sqrt(0.5)')
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Gain')
    plt.grid(True)
    plt.legend(loc = 'best')
    
    

