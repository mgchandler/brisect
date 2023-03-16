# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 10:43:32 2022
@author: xs16051
"""

__author__ = "Xiaoyu Sun, University of Bristol (UoB)"
__copyright__ = "UoB, August 2022"
__version__ = "FMC_Acquisition_XS1.0"

import os
os.system('cls')

# 3rd party imports
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.signal import butter
from fn_create_hanning_burst import *  # Upload Functions
# from scipy.signal import freqz
# from scipy.signal import chirp

# local imports
from ultrasonic_matrix import matrix_controller

# ----- Butterworth Filter Function -----
def butter_bandpass(lowcut, highcut, fs, order):
    return butter(order, [lowcut, highcut], fs=fs, btype='band')

def butter_bandpass_filter(data, lowcut, highcut, fs, order):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

# Create and configure an Ultrasonic Matrix object
# The AD2 is configured to have a 8k analogue input buffer.
# At 100MHz sample rate, the comms link is quickly saturated
# so the buffer size is the effective limit on acquisition time
# at 100MHz, it is 80us

# ----- Script -----
pulse_shape = "custom" # 1. "square" 2. "sine" 3. "custom"
pulse_cycle = 10
pulse_volt = 10
centre_freq = 40e3
sample_freq = 1e6
velocity = 343;

# ----- Single Pitch-Catch Mode Measurement (SMA Channels) -----
ch_tx = 0 # To use the SMA port
ch_rx = 0 # To use the SMA port

# acq_time = ((100e6) / sample_freq) * (80e-6)
max_time_pts = 4096
acq_time = max_time_pts / sample_freq
time_axis = np.arange(max_time_pts) / sample_freq
dist_axis = time_axis * (velocity / 2)

# ----- Custom Waveform -----
burst_time_pts = 4096
DAC_freq=10E6##Frequency of the output DAC, rather than the ADC
time_step = 1 / DAC_freq
centre_time = 0

in_time, in_time_sig, in_freq, in_freq_spec, fft_pts = fn_create_hanning_burst(burst_time_pts, centre_freq, time_step, pulse_cycle, centre_time)
dist_axis = time_axis * (velocity / 2)

if pulse_shape == 'custom':
    self_waveform = in_time_sig
    pulse_cycle=1   #Only a single waveform 'recording' per transmission
    centre_freq=int(1/(time_step*burst_time_pts))   ##Frequency is for the whole waveform recording - not a single cycle
else:
    self_waveform = []
    
# plt.plot(in_time*1e3, self_waveform, color = 'red', linestyle = "-", label = 'Input Signal')
# plt.ylim([-20, 20])
# plt.legend()
# plt.xlabel('Time (ms)')
# plt.ylabel('Amplitude (V)')
# plt.show()



for kk in range(1, 10, 1):
    usm = matrix_controller.usm(
        tx_channel = ch_tx,
        rx_channel = ch_rx,
        drive_frequency = centre_freq,
        drive_shape = pulse_shape,
        custom_waveform = self_waveform,
        abs_drive_v = pulse_volt,
        num_drive_cycles = pulse_cycle,
        sample_rate = sample_freq,
        max_meas_voltage_vpp = 5,
        trigger_v = 0.5,
        trigger_time_s = 0,
        acq_time_ms = acq_time * 1e3)
    
    results = usm.acquire_measurement()
    
    # ----- !!! Close the Deivce before Data Processing !!! -----
    usm.close()

    # ----- Format Array Results -----
    time_data = np.fromiter(results[2:], dtype = float)
    
    # ----- Print Cycle -----
    print(kk)

# ----- Add Bandpass Filter -----
lowcut = 30e3
highcut = 50e3
order = 5

data_fltr = butter_bandpass_filter(time_data, lowcut, highcut, sample_freq, order)

# ----- Plot Signal -----
# plt.plot(dist_axis*1e2, time_data, color = 'black', linestyle = "-", label = 'Received Data')
plt.plot(dist_axis*1e2, data_fltr, color = 'blue', linestyle = "-", label = 'Filtered Data')
plt.ylim([-0.2, 0.2])
plt.legend()
plt.xlabel('Distance (cm)')
plt.ylabel('Amplitude (V)')
plt.show()

# ----- Save Data as .txt File -----
# =============================================================================
# np.savetxt('record_sma_time_data.txt', time_data, delimiter = ',')
# np.savetxt('record_sma_data_fltr.txt', data_fltr, delimiter = ',')
# np.savetxt('record_sma_time.txt', time_axis, delimiter = ',')
# =============================================================================

# ----- Save Data as .csv File -----
# =============================================================================
# f = open("record1.csv", "w")
# for v in results:
#     f.write("%s\n" % v)
# f.close()
# =============================================================================
