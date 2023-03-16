"""
Example usage of Ultrasonic Matrix Controller - basic features

This script uses some very basic features of the Ultrasonic Matrix Controller,
for debugging purposes
"""

__author__ = "Andrew Palmer, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort Design Ltd., July 2022"
__version__ = "0.2.0"

# stdlib imports
import sys

# 3rd party imports
import matplotlib.pyplot as plt
import numpy as np
import time

# local imports
from ultrasonic_matrix import matrix_controller
from filterFunction import applyFilter
from resultsPlot import singlePlot, multPlot,FFT_plot
from SNR_measurement import SNR_measurement

# output logging levels
INFO_OUTPUT = 1  # production logging output
WARN_OUTPUT = 0  # non-critical errors
ERROR_OUTPUT = 1  # critical errors
DEV1_OUTPUT = 0  # first level debug output
DEV2_OUTPUT = 0  # second level debug output


if DEV1_OUTPUT:
    print(
        sys.argv[0], ", installed python version: ", sys.version_info.major,
        '.', sys.version_info.minor, sep='')
    
    
plt.close('all')##Close all existing plots

fs=600000   ##Set sampling frequency

# Create and configure an Ultrasonic Matrix object
usm = matrix_controller.usm(
    tx_channel=2, rx_channel=24, drive_frequency=39500,
    drive_shape="sine", num_drive_cycles=10,
    acq_time_ms=35,sample_rate=fs)
    
# Only the "tx_channel" and "rx_channel" are required for the creation of
# a usm object. All the rest have default values, as listed below:
"""

usm = matrix_controller.usm(
    tx_channel, rx_channel,
    abs_drive_v=5,
    drive_shape="square",
    custom_waveform=[],
    max_meas_voltage_vpp=5,
    trigger_v=0.5,
    trigger_time_s=-0.001,
    drive_frequency=40000,
    num_drive_cycles=10,
    sample_rate=400000,
    acq_time_ms=30)

"""

# An acquisition can be done at this point, as device is fully configured
# and initialised
results = usm.acquire_measurement()

######### Example of how to do a single acquisition #############

##Setup tx and rx channels
usm.set_multiplexer_channel(tx_channel=2, rx_channel=24)

# # Re-configure the wavegen with a different drive shape and frequency
usm.config_wavegen(
      abs_drive_v=10, drive_shape="sine", drive_frequency=39500,
      num_drive_cycles=10)
# time.sleep(0.01)

##Perform acquisition
results1 = usm.acquire_measurement()

# print("Results, measurement header info: ")
print(str(results1[0]))
print(str(results1[1]))

##Apply filter to results
filtered_results= applyFilter(fs,results1[2:])

##Generate a plot of a single result
singlePlot(results1,filtered_results,fs)

# ##Plot the FFT of the acquisition
# FFT_plot(results1[2:],filtered_results,fs)

# #Calculate SNR
# print("Raw Signal SNR")
# raw_SNR_dB= SNR_measurement(results1[2:],0.002,0.0023,0.0025,0.003,fs,usm.trigger_time_s,1)
# print("")
# print("Filtered Signal SNR")
# filt_SNR_db= SNR_measurement(filtered_results,0.002,0.0023,0.0025,0.003,fs,usm.trigger_time_s,1)


# ##Write out the raw and the filtered output to a csv
# f = open("raw_output.csv", "w")
# for v in results1:
#     f.write("%s\n" % v)
# f.close()

# f = open("filt_output.csv", "w")
# ##Copy across header info from raw results
# f.write("%s\n" % results1[0])
# f.write("%s\n" % results1[1])
# for v in filtered_results:
#     f.write("%s\n" % v)
# f.close()

######Example of how to do a parameter sweep and plot multiple results ###

#Generate combined plots of multiple scans with varying parameters
# fig2=plt.figure(figsize=(12, 10), dpi=100)
# ##Create subplots and link axis (allows them to be zoomed together)
# ax1= plt.subplot(2,1,1)
# ax2=plt.subplot(2,1,2,sharex=ax1,sharey=ax1)

# ##Array containing the number of cycles for each acquisition
# numCyclesArray=[3,5,20,40]

# for i in range(0,4):
    
#     # usm.set_multiplexer_channel(tx_channel=43, rx_channel=i) 
#     usm.config_wavegen(
#       abs_drive_v=10, drive_shape="sine", drive_frequency=39000,
#       num_drive_cycles=numCyclesArray[i])
    
#     ##acquire measurement
#     results1 = usm.acquire_measurement()
    
#     ##apply filter
#     filtered_results= applyFilter(fs,results1[2:])
    
#     ##create label text for multi-plot legend
#     label_text="Num Cycles="+str(numCyclesArray[i])
    
#     ##Add data to the plot
#     multPlot(fig2,ax1,ax2,results1,filtered_results,fs,label_text)
    
# ##Appy final formatting to the multiplot and save
# fig2.tight_layout()
# plt.xlabel("WaveGen Cycle Count")
# plt.ylabel("Signal Amplitude (V)")
# # plt.xticks(numCyclesArray)
# plt.legend(loc="lower right")
    
# plt.savefig('multPlot.png')

# Need to close the device, to free it up for any other program
usm.close()
