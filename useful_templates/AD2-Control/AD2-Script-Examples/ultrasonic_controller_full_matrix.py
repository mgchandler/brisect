"""
Example "Full Matrix Capture" usage of Ultrasonic Matrix Controller

"""

__author__ = "Andrew Palmer, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort Design Ltd., August 2022"
__version__ = "0.1.0"

# stdlib imports
import sys


# 3rd party imports
import matplotlib.pyplot as plt
import numpy
import time

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
usm = matrix_controller.usm(
    tx_channel=2, rx_channel=24, drive_frequency=39500,
    drive_shape="sine", num_drive_cycles=10,
    acq_time_ms=5)

# Make a measurement from each possible receiver for one transmitter
results_combo1 = []
tx_channel = 2
for rx_channel in range(1, 64+1):
    if rx_channel != tx_channel:
        usm.set_multiplexer_channel(
            tx_channel=tx_channel, rx_channel=rx_channel)
        time.sleep(0.01) ##May only be required if no ultrasound transducer on channel
        results_combo1.append(usm.acquire_measurement())

plt.figure()
for a in range(0,63):
    plt.plot(results_combo1[a][2:],label=results_combo1[a][1][1])
    
plt.legend(loc="lower right")

# Make a measurement from each possible receiver for each possible transmitter
results_combo2 = []

for tx_channel in range(1, 64 + 1):
    #print("combo 2, tx channel: ", tx_channel)
    for rx_channel in range(1, 64 + 1):
        if rx_channel != tx_channel:
            usm.set_multiplexer_channel(
                tx_channel=tx_channel, rx_channel=rx_channel)
            time.sleep(0.01) ##May only be required if no ultrasound transducer on channel
            results_combo2.append(usm.acquire_measurement())

# Need to close the device, to free it up for any other program
usm.close()

print("\nCombo 1, number of acquisitions: ", str(len(results_combo1)))
# there are 4032 permutations of 2 elements from 64 items
print("\nCombo 2, number of acquisitions: ", str(len(results_combo2)))


