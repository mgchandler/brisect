"""
Example usage of setting a custom waveform in the Ultrasonic Matrix Controller

"""

__author__ = "Andrew Palmer, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort Design Ltd., August 2022"
__version__ = "0.1.0"

# stdlib imports
import sys

# 3rd party imports
import matplotlib.pyplot as plt
from scipy.signal import chirp
import numpy as np

# local imports
from ultrasonic_matrix import matrix_controller

# output logging levels
INFO_OUTPUT = 1  # production logging output
WARN_OUTPUT = 0  # non-critical errors
ERROR_OUTPUT = 1  # critical errors
DEV1_OUTPUT = 0  # first level debug output
DEV2_OUTPUT = 0  # second level debug output


if DEV1_OUTPUT:
    print(sys.argv[0], ", installed python version: ", sys.version_info.major,
          '.', sys.version_info.minor, sep='')

MAX_NUM_WAVEGEN_SAMPLES = 4096


# Create and configure an Ultrasonic Matrix object

pulse_shape = "sine"
pulse_cycle = 5
pulse_volt = 10
centre_freq = 5e6
sample_freq = 100e6

ch_tx = 1
ch_rx = 2
ch_num = 18

ratio_buffer_length = (80*1e-6) / (100*1e6) # 100MHz - 80us
acq_time = sample_freq * ratio_buffer_length
max_time_pts = int((sample_freq ** 2) * ratio_buffer_length)
time_axis = np.arange(max_time_pts) / sample_freq

usm = matrix_controller.usm(
    tx_channel = ch_tx, # No meaning if 'usm.set_multiplexer_channel' used later
    rx_channel = ch_rx, # No meaning if 'usm.set_multiplexer_channel' used later
    drive_frequency = centre_freq,
    drive_shape = pulse_shape,
    abs_drive_v = pulse_volt,
    num_drive_cycles = pulse_cycle,
    sample_rate = sample_freq,
    max_meas_voltage_vpp = 5,
    trigger_v = 0.5,
    trigger_time_s = 0,
    acq_time_ms = acq_time * 1e3)
    

# some custom waveform ideas
# Values must be from -1.0 (-ve full scale output) to +1.0 (+ve full scale o/p)
# custom_waveform = [0, 0.5, 0.2]
# ustom_waveform = [0, -0.5, -1, -0.5, 0, 0.5, 1, 0.5]

# create custom waveform - a chirp
# resulting instantaneous frequency is approx.
# linspace max time (here, 10) * chirp f * drive_frequency
times = np.linspace(0, 10, MAX_NUM_WAVEGEN_SAMPLES)

# chirp example 1
# first cycle is approx 10kHz, last is approx. 25kHz
custom_waveform = chirp(times, f0 = 10, f1 = 40, t1 = 10, method = "linear")

plt.plot(np.fromiter(custom_waveform, dtype = float), color='blue')
plt.show()


# need to call set_custom_waveform, in addition to calling "config_wavegen"
# with the drive_shape set to "custom"
# (as well as any other parameters as desired).

usm.set_custom_waveform(custom_waveform)

usm.config_wavegen(
    abs_drive_v = 4,
    drive_shape = "custom",
    drive_frequency = centre_freq,
    num_drive_cycles = 1)

results = usm.acquire_measurement()

# Need to close the device, to free it up for any other program
usm.close()

print("\nResults, measurement header info: ")
print(str(results[0]))
print(str(results[1]))

# Plot some of the results
# ignore the headers
plt.plot(np.fromiter(results[2:], dtype = float), color='orange')
plt.show()

# Write one result to csv
f = open("record1.csv", "w")
for v in results:
    f.write("%s\n" % v)
f.close()
