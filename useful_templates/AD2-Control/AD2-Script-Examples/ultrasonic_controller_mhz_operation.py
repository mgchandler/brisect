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
import numpy
# from scipy.signal import chirp

# local imports
from ultrasonic_matrix import matrix_controller

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


# Create and configure an Ultrasonic Matrix object
# The AD2 is configured to have a 8k analogue input buffer.
# At 100MHz sample rate, the comms link is quickly saturated
# so the buffer size is the effective limit on acquisition time
# at 100MHz, it is 80us

usm = matrix_controller.usm(
    tx_channel = 0,
    rx_channel = 0,
    sample_rate = 100e6,
    drive_frequency = 2.25e6,
    trigger_time_s = 0,
    drive_shape = "square",
    num_drive_cycles = 5,
    acq_time_ms = 0.08)

results = usm.acquire_measurement()

# Close the device to free it up for any other programs
usm.close()

print("\nResults, measurement header info: ")
print(str(results[0]))
print(str(results[1]))

# Plot some of the results
# ignore the headers
plt.plot(numpy.fromiter(results[2:], dtype = float), color='orange')
plt.show()

# Write one result to csv
f = open("record1.csv", "w")
for v in results:
    f.write("%s\n" % v)
f.close()
