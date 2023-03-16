"""
API for Ultrasonic Matrix Controller

Glossary:
"Channel" - a number between 1 and 64, corresponding to a transducer
"Group" - The set of channels for each function (ie, rx/tx) is split across
two 32-way multiplexers. The "group" refers to which multiplexer
is being used.

class usm - an Ultrasonic Matrix object

usm.__init__( tx_channel, rx_channel, abs_drive_v,
    drive_shape, custom_waveform, max_meas_voltage_vpp, trigger_v,
    trigger_time_s, drive_frequency, num_drive_cycles,
    sample_rate, acq_time_ms
):
    Opens device and sets configuration provided. Any values not
    provided (except tx and rx channels, which are obligatory) are set
    to hard-coded default values.

usm.set_pos_vout(voltage):
    Sets positive supply output voltage

usm.set_neg_vout(voltage):
    Sets negative supply output voltage

usm.set_multiplexer_channel(function, channel):
    Sets the output channel for function to channel, function being "rx" or
    "tx", and channel between 1 and 64

usm.set_custom_waveform(wavegen_samples):
    Loads the supplied custom waveform into the device.

usm.config_wavegen(
    abs_drive_v, drive_shape, drive_frequency, num_drive_cycles
):
    Re-configures waveform generator with supplied parameters

usm.acquire_measurement():
    Performs one measurement acquisition with currently-configured values

usm.close():
    Closes device, allowing re-use by other programs.

"""

__author__ = "Andrew Palmer, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort, 2022-07-12 (yyyy-mm-dd)"


# stdlib imports
import ctypes
import sys
import os
import time

# 3rd party imports
import numpy as np

# local imports


# output logging levels
INFO_OUTPUT = 1  # production logging output
WARN_OUTPUT = 0  # non-critical errors
ERROR_OUTPUT = 1  # critical errors
DEV1_OUTPUT = 0 # first level debug output
DEV2_OUTPUT = 0  # second level debug output

# configurable through API
DEFAULT_ABS_DRIVE_VOLTAGE = 5
DEFAULT_DRIVE_WAVEFORM = "square"
DEFAULT_DRIVE_CYCLE_NUM = 10
DEFAULT_SAMPLE_RATE = 400000
DEFAULT_DRIVE_FREQUENCY = 40000
DEFAULT_ACQ_TIME_MS = 30
DEFAULT_MAX_MEAS_VOLTAGE_VPP = 5 # TODO check we have this right w/double-ended signals, etc
DEFAULT_TRIGGER_TIME_S = -0.001 # recording starts after this delay value
DEFAULT_TRIGGER_V = 0.5


# not configurable through API
DEFAULT_TRIGGER_HYST_V = 0.000001
DEFAULT_AUTO_TRIGGER_TIMEOUT_S = 0
DEFAULT_MULTIPLEXER_BUS_FREQ = 50000
DEFAULT_POS_VOUT_V = 5
DEFAULT_NEG_VOUT_V = -5

multiplexer_1_transducers = (1, 32)
multiplexer_2_transducers = (33, 64)

if sys.platform.startswith("win"):
    dwf = ctypes.cdll.dwf
    constants_path = "C:" + os.sep + "Program Files (x86)" + os.sep \
    + "Digilent" + os.sep + "WaveFormsSDK" + os.sep \
    + "samples" + os.sep + "py"
elif sys.platform.startswith("darwin"):
    dwf = ctypes.cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
    constants_path = os.sep + "Applications" + os.sep + "WaveForms.app" \
    + os.sep + "Contents" + os.sep + "Resources" + os.sep + "SDK" + os.sep \
    + "samples" + os.sep + "py"
else:
    dwf = ctypes.cdll.LoadLibrary("libdwf.so")
    constants_path = os.sep + "usr" + os.sep + "share" + os.sep \
    + "digilent" + os.sep + "waveforms" + os.sep + "samples" + os.sep + "py"

# Import Digilent WaveForms constants
sys.path.append(constants_path)
import dwfconstants as constants


class usm():
    """
    Public class for high-level control of Ultrasonic Matrix hardware

    Initialisation includes 2 second stabilisation time after all config is
    applied
    
    There are two multiplexers for rx and two for tx - these are 32-way
    multiplexers, covering the total of 64 transducers. This is called the
    "rx_group" and "tx_group" in this module.
    
    Each group has its own port on the AD2 - there are two Analogue Inputs
    active, one for each rx group. There are two Analogue Outputs used as
    waveform generators - these are selectively enabled/disabled as needed,
    depending on the tx_group value.
    
    ADCIN1 handles transducers 1 to 32, ADCIN2 handles 33 to 64

    """
    
    def __init__(
        self, tx_channel, rx_channel, abs_drive_v=DEFAULT_ABS_DRIVE_VOLTAGE,
        drive_shape=DEFAULT_DRIVE_WAVEFORM,
        custom_waveform=[],
        max_meas_voltage_vpp=DEFAULT_MAX_MEAS_VOLTAGE_VPP,
        trigger_v=DEFAULT_TRIGGER_V,
        trigger_time_s=DEFAULT_TRIGGER_TIME_S,
        drive_frequency=DEFAULT_DRIVE_FREQUENCY,
        num_drive_cycles=DEFAULT_DRIVE_CYCLE_NUM,
        sample_rate=DEFAULT_SAMPLE_RATE, acq_time_ms=DEFAULT_ACQ_TIME_MS
    ):
        # configure API values
        self.abs_drive_v = abs_drive_v
        self.drive_shape = drive_shape
        self.num_drive_cycles = num_drive_cycles
        self.drive_frequency = drive_frequency
        self.max_meas_voltage_vpp = max_meas_voltage_vpp
        self.sample_rate = sample_rate
        self.acq_time_ms = acq_time_ms
        self.trigger_v = trigger_v
        self.trigger_time_s = trigger_time_s
        
        
        # configure internal values
        self.auto_trigger_timeout_s = DEFAULT_AUTO_TRIGGER_TIMEOUT_S
        self.trigger_hyst_v = DEFAULT_TRIGGER_HYST_V
        self.multiplexer_bus_freq = DEFAULT_MULTIPLEXER_BUS_FREQ
        self.pos_vout_v = DEFAULT_POS_VOUT_V
        self.neg_vout_v = DEFAULT_NEG_VOUT_V
        self.min_acq_buffer_size = ctypes.c_int(0)
        self.max_acq_buffer_size = ctypes.c_int(0)
        self.min_wave_gen_samples = ctypes.c_int(0)
        self.max_wave_gen_samples = ctypes.c_int(0)
        self.num_capture_channels = ctypes.c_int(0)
        
        # 4096 is the maximum available with the device in "config 1"
        # as we want to iniialise the data structure here, we will use this
        # hardcoded value
        self.max_num_wavegen_samples = 4096
        self.num_wavegen_samples = 0
        self.wavegen_samples = (ctypes.c_double * 1)()
        
        self.set_custom_waveform(custom_waveform)

        self.acq_num_samples = ctypes.c_int(
            int((self.sample_rate * self.acq_time_ms) / 1000))
        
        self.drive_time_s = self.num_drive_cycles / self.drive_frequency
        
        self.sys_freq = ctypes.c_double()
        
        self.device_handle = ctypes.c_int(0)
        
        self.tx_channel = 0
        self.rx_channel = 0
        self.tx_group = 0
        self.rx_group = 0
        
        # size of multiplexer control message
        # bytes 0 and 5 are used to pad data output
        # around the clear and latch pulses
        # bytes 1 - 4 are the shift regiser data
        self.num_multiplexer_bus_message_bits = 144

        # "clear" pulse, and trailing "latch" pulse
        self.clear_data = (18 * ctypes.c_byte)(*[
            0x80, # "clear" pulse
            0x00, 0x00, 0x00, 0x00, # data bytes for all multiplexers
            0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,0x00,
            0x00, 0x00, 0x00, 0x00]) # for "latch" pulse
        self.latch_data = (18 * ctypes.c_byte)(*[
            0xFF,
            0xFF, 0xFF, 0xFF, 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF,0xFF,
            0xFF, 0xFF, 0xFF, 0xFE])

        self.set_multiplexer_channel(tx_channel, rx_channel)
        
        version = ctypes.create_string_buffer(16)
        dwf.FDwfGetVersion(version)
        if DEV1_OUTPUT:
            print("DWF Version: "+str(version.value))

        # enumerate AD2 devices
        devices = ctypes.c_int(0)
        configs = ctypes.c_int(0)
        retVal = ctypes.c_int(0)
        dwf.FDwfEnum(constants.devidDiscovery2, ctypes.byref(devices))
        if DEV1_OUTPUT:
            print(
                "matrix_controller::init, number of AD2 devices found: ",
                str(devices.value), sep='')
        # ask first device to enumerate config list
        dwf.FDwfEnumConfig(1, ctypes.byref(configs))
        
        # get max analogue buffer size in config 1
        dwf.FDwfEnumConfigInfo(0, constants.DECIAnalogInBufferSize, ctypes.byref(retVal))
        
        if DEV1_OUTPUT:
            print(
                "First AD2, max analogue buffer size in config 1: ",
                str(retVal.value), sep='')
        
        # and in config 2
        dwf.FDwfEnumConfigInfo(1, constants.DECIAnalogInBufferSize, ctypes.byref(retVal))
        
        if DEV1_OUTPUT:
            print(
                "First AD2, max analogue buffer size in config 2: ",
                str(retVal.value), sep='')
        # connect to first available AD2
        # Open using second config, to maximise analgoue input buffer size
#        dwf.FDwfDeviceConfigOpen(
#            ctypes.c_int(-1), 1,  ctypes.byref(self.device_handle))

        # Can't actually do that, as we lose the "patterns" buffer, which is
        # needed for multiplexer control
        dwf.FDwfDeviceOpen(
            ctypes.c_int(-1),  ctypes.byref(self.device_handle))

        if self.device_handle.value == 0:
            if ERROR_OUTPUT:
                print(
                    "matrix_controller::usm::init, ",
                    "ERROR: Failed to open device. ")
            szerr = ctypes.create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print("\nError message from device: ", str(szerr.value))
            quit()

        if (
            self.device_handle.value > 0
            and self.tx_group > 0
            and self.rx_group > 0
        ):
            # get allowable buffer sizes
            dwf.FDwfAnalogInBufferSizeInfo(
                self.device_handle, ctypes.byref(self.min_acq_buffer_size),
                ctypes.byref(self.max_acq_buffer_size))
                
            # get number of channels
            dwf.FDwfAnalogInChannelCount(
                self.device_handle, ctypes.byref(self.num_capture_channels))

            # get inernal clock frequency
            dwf.FDwfDigitalOutInternalClockInfo(
                self.device_handle, ctypes.byref(self.sys_freq))
            
            if DEV1_OUTPUT:
                print(
                    "\nmatrix_controller::usm::init",
                    "\ndevice handle: ",
                    str(self.device_handle.value),
                    "\nnum samples to get: ", str(self.acq_num_samples.value),
                    ", num capture channels: ",
                    str(self.num_capture_channels.value),
                    "\ntx group: ", str(self.tx_group),
                    ", rx group: ", str(self.rx_group),
                    "\nmin device acquire buffer size: ",
                    str(self.min_acq_buffer_size.value),
                    ", max device acquire buffer size: ",
                    str(self.max_acq_buffer_size.value),
                    "\nAD2 Digital Out internal clock frequency: ",
                    str(self.sys_freq.value),
                    "\ndrive waveform active time: ", str(self.drive_time_s),
                    "\nnum supplied wavegen samples: ",
                    str(self.num_wavegen_samples), sep='')
            
            if DEV2_OUTPUT:
                print(
                    "\nWavegen samples: ", list(self.wavegen_samples))
            # device config
            
            # enable power supply outputs
            self.set_pos_vout(self.pos_vout_v)
            self.set_neg_vout(self.neg_vout_v)
            
            # Allow time for +/-15V rail to rise
            time.sleep(1)  # 1s
                
            # enable waveform generator on correct output channel
            # (which are 0-indexed on the AD2)
            dwf.FDwfAnalogOutNodeEnableSet(
                self.device_handle, ctypes.c_int(self.tx_group - 1),
                constants.AnalogOutNodeCarrier, ctypes.c_bool(True))
            
            # get number of available custom waveform generator samples
            dwf.FDwfAnalogOutNodeDataInfo(
                self.device_handle, ctypes.c_int(0),
                constants.AnalogOutNodeCarrier,
                ctypes.byref(self.min_wave_gen_samples),
                ctypes.byref(self.max_wave_gen_samples))
            
            if DEV2_OUTPUT:
                print(
                    "\nmatrix_controller::usm::init",
                    "\nmin number of custom waveform samples: ",
                    str(self.min_wave_gen_samples.value),
                    ", max number of custom waveform samples: ",
                    str(self.max_wave_gen_samples.value), sep='')
                    
            # configure signal capture (oscilloscope)
            
            # enable both analogue input channels
            # "analgoue in" channels are zero-indexed
            dwf.FDwfAnalogInChannelEnableSet(
                self.device_handle, ctypes.c_int(0),
                ctypes.c_bool(True))
                
            dwf.FDwfAnalogInChannelEnableSet(
                self.device_handle, ctypes.c_int(1),
                ctypes.c_bool(True))
        
            # set offset voltage
            dwf.FDwfAnalogInChannelOffsetSet(
                self.device_handle, ctypes.c_int(-1),
                ctypes.c_double(0))
            
            # set voltage range
            dwf.FDwfAnalogInChannelRangeSet(
                self.device_handle, ctypes.c_int(-1),
                ctypes.c_double(self.max_meas_voltage_vpp))

            # set the buffer size
            dwf.FDwfAnalogInBufferSizeSet(
                self.device_handle, self.max_acq_buffer_size)
            
            # set the acquisition frequency (in Hz)
            dwf.FDwfAnalogInFrequencySet(
                self.device_handle, ctypes.c_double(self.sample_rate))
            
            # disable averaging on all enabled channels
            dwf.FDwfAnalogInChannelFilterSet(
                self.device_handle, ctypes.c_int(-1),
                constants.filterDecimate)
            
            # set to record mode
            dwf.FDwfAnalogInAcquisitionModeSet(
                self.device_handle, constants.acqmodeRecord)
            
            # set record length
            dwf.FDwfAnalogInRecordLengthSet(
                self.device_handle, ctypes.c_double(self.acq_time_ms / 1000))
            
            # config trigger
            # horizontal trigger point
            dwf.FDwfAnalogInTriggerPositionSet(
                self.device_handle, ctypes.c_double(self.trigger_time_s))

            # Set the trigger source
            # The below sets "Normal" trigger mode, in conjunction with
            # auto timeout set to 0
            if self.tx_group == 1:
                dwf.FDwfAnalogInTriggerSourceSet(
                    self.device_handle, constants.trigsrcAnalogOut1)
            elif self.tx_group == 2:
                dwf.FDwfAnalogInTriggerSourceSet(
                    self.device_handle, constants.trigsrcAnalogOut2)

            dwf.FDwfAnalogInTriggerAutoTimeoutSet(
                self.device_handle,
                ctypes.c_double(self.auto_trigger_timeout_s))

            dwf.FDwfAnalogInTriggerTypeSet(
                self.device_handle, constants.trigtypeEdge)
                
            dwf.FDwfAnalogInTriggerConditionSet(
                self.device_handle, constants.DwfTriggerSlopeRise)
            
            # not needed if we are triggering from waveform gen o/p
#            dwf.FDwfAnalogInTriggerChannelSet(
#                self.device_handle, ctypes.c_int(self.rx_group - 1))

            dwf.FDwfAnalogInTriggerLevelSet(
                self.device_handle, ctypes.c_double(self.trigger_v))

            dwf.FDwfAnalogInTriggerHysteresisSet(
                self.device_handle, ctypes.c_double(self.trigger_hyst_v))
            
            # configure digital outputs for multiplexer control bus
            # set run time
            dwf.FDwfDigitalOutRunSet(
                self.device_handle, ctypes.c_double(
                    self.num_multiplexer_bus_message_bits
                    / self.multiplexer_bus_freq))

            # DIO pins on AD2 are 3v3, and 5v tolerant in open-drain mode
            # enable that now on all outputs, as we are using a 5v multiplexer
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(0),
                constants.DwfDigitalOutOutputOpenDrain)
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(1),
                constants.DwfDigitalOutOutputOpenDrain)
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(2),
                constants.DwfDigitalOutOutputOpenDrain)
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(3),
                constants.DwfDigitalOutOutputOpenDrain)
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(4),
                constants.DwfDigitalOutOutputOpenDrain)
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(5),
                constants.DwfDigitalOutOutputOpenDrain)
            dwf.FDwfDigitalOutOutputSet(
                self.device_handle, ctypes.c_int(6),
                constants.DwfDigitalOutOutputOpenDrain)
            
            # DIO 0 - Data
            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(0), ctypes.c_int(1))
            dwf.FDwfDigitalOutTypeSet(
                self.device_handle, ctypes.c_int(0),
                constants.DwfDigitalOutTypeCustom)
            
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(0),
                constants.DwfDigitalOutIdleLow)

            # sets initial divider value - when expires, moves to main value
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(0), ctypes.c_int(
                    int(self.sys_freq.value / self.multiplexer_bus_freq)))

            # main value of divider when running
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(0), ctypes.c_int(
                    int(self.sys_freq.value / self.multiplexer_bus_freq)))

            # DIO 1 - Clock
            
            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(1), ctypes.c_int(1))
            # handle, channel, idle set
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(1),
                constants.DwfDigitalOutIdleLow)

            # sets initial counter and level values
            # handle, channel, start high?, divider initial value
            dwf.FDwfDigitalOutCounterInitSet(
                self.device_handle, ctypes.c_int(1), ctypes.c_int(0),
                ctypes.c_int(1))

            # main values of counter and level when running
            # "On counter expiration the level is toggled, and this directs
            # the low or high value loading. In case one of these is zero,
            # the level is not toggled."
            # handle, channel, counter low value, counter high value
            dwf.FDwfDigitalOutCounterSet(
                self.device_handle, ctypes.c_int(1), ctypes.c_int(1),
                ctypes.c_int(1))

            # sets initial divider value - when expires, moves to main value
            # this could be used to delay the clock until the clear pulse has
            # been sent
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(1), ctypes.c_int(
                    int(self.sys_freq.value 
                        / (self.multiplexer_bus_freq * 2))))

            # set main divider twice of bus frequency
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(1), ctypes.c_int(
                    int(self.sys_freq.value 
                        / (self.multiplexer_bus_freq * 2))))

            # DIO 2 - Clear (min width is 55ns, period at 50kHz is 20us)
            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(2), ctypes.c_int(1))
            dwf.FDwfDigitalOutTypeSet(
                self.device_handle, ctypes.c_int(2),
                    constants.DwfDigitalOutTypeCustom)
            
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(2),
                constants.DwfDigitalOutIdleLow)

            # sets initial divider value - when expires, moves to main value
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(2), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))

            # main value of divider when running
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(2), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))

            # DIO 3 - !(MUX1 latch enable) (min width is 55ns at 3v)
            # period at chosen 50kHz is 20us

            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(3), ctypes.c_int(1))
            dwf.FDwfDigitalOutTypeSet(
                self.device_handle, ctypes.c_int(3),
                constants.DwfDigitalOutTypeCustom)
            
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(3),
                constants.DwfDigitalOutIdleHigh)

            # sets initial divider value - when expires, moves to main value
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(3), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))

            # main value of divider when running
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(3), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))
                    
            # DIO 4 - !(MUX2 latch enable) (min width is 55ns at 3v)
            # period at chosen 50kHz is 20us

            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(4), ctypes.c_int(1))
            dwf.FDwfDigitalOutTypeSet(
                self.device_handle, ctypes.c_int(4),
                constants.DwfDigitalOutTypeCustom)
            
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(4),
                constants.DwfDigitalOutIdleHigh)

            # sets initial divider value - when expires, moves to main value
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(4), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))

            # main value of divider when running
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(4), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))
            # now that eveything is configured, disable auto configure
            dwf.FDwfDeviceAutoConfigureSet(
                self.device_handle, ctypes.c_bool(False))
            
            # DIO 5 - !(MUX3 latch enable) (min width is 55ns at 3v)
            # period at chosen 50kHz is 20us

            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(5), ctypes.c_int(1))
            dwf.FDwfDigitalOutTypeSet(
                self.device_handle, ctypes.c_int(5),
                constants.DwfDigitalOutTypeCustom)
            
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(5),
                constants.DwfDigitalOutIdleHigh)

            # sets initial divider value - when expires, moves to main value
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(5), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))

            # main value of divider when running
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(5), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))
                    
            # DIO 6 - !(MUX4 latch enable) (min width is 55ns at 3v)
            # period at chosen 50kHz is 20us

            # handle, channel, enable
            dwf.FDwfDigitalOutEnableSet(
                self.device_handle, ctypes.c_int(6), ctypes.c_int(1))
            dwf.FDwfDigitalOutTypeSet(
                self.device_handle, ctypes.c_int(6),
                constants.DwfDigitalOutTypeCustom)
            
            dwf.FDwfDigitalOutIdleSet(
                self.device_handle, ctypes.c_int(6),
                constants.DwfDigitalOutIdleHigh)

            # sets initial divider value - when expires, moves to main value
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerInitSet(
                self.device_handle, ctypes.c_int(6), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))

            # main value of divider when running
            # handle, channel, divider value
            dwf.FDwfDigitalOutDividerSet(
                self.device_handle, ctypes.c_int(6), ctypes.c_int(
                    int(self.sys_freq.value 
                        / self.multiplexer_bus_freq)))
            # now that eveything is configured, disable auto configure
            dwf.FDwfDeviceAutoConfigureSet(
                self.device_handle, ctypes.c_bool(False))

            # wait at least 2 seconds for the offset to stabilize
            # after device open or a range change
            time.sleep(2)

        elif ERROR_OUTPUT:
            print(
                "\nmatrix_controller::usm::init ERROR, ",
                "unable to initialise instruments",
                sep='')

    def set_pos_vout(self, pos_vout_v):
        if DEV1_OUTPUT:
            print("\nmatrix_controller::usm::set_pos_vout, new voltage:",
                str(pos_vout_v))
        self.pos_vout_v = pos_vout_v
        # enable positive supply
        # handle, channel, node ("function"), value
        dwf.FDwfAnalogIOChannelNodeSet(
            self.device_handle, ctypes.c_int(0), ctypes.c_int(0),
            ctypes.c_double(True))
        # set voltage
        dwf.FDwfAnalogIOChannelNodeSet(
            self.device_handle, ctypes.c_int(0), ctypes.c_int(1),
            ctypes.c_double(self.pos_vout_v))
        # master enable
        dwf.FDwfAnalogIOEnableSet(self.device_handle, ctypes.c_int(1))


    def set_neg_vout(self, neg_vout_v):
        if DEV1_OUTPUT:
            print("\nmatrix_controller::usm::set_neg_vout, new voltage:",
                str(neg_vout_v))
        self.neg_vout_v = neg_vout_v
        
        # enable negative supply
        # handle, channel, node ("function"), value
        dwf.FDwfAnalogIOChannelNodeSet(
            self.device_handle, ctypes.c_int(1), ctypes.c_int(0),
            ctypes.c_double(True))
        # set voltage
        dwf.FDwfAnalogIOChannelNodeSet(
            self.device_handle, ctypes.c_int(1), ctypes.c_int(1),
            ctypes.c_double(self.neg_vout_v))
        # master enable
        dwf.FDwfAnalogIOEnableSet(self.device_handle, True)

    def set_multiplexer_channel(self, tx_channel, rx_channel):
        # channel value is from 1 to 64
        # Send HV2801 shift register data
        
        #Create blank arrays for all 6 data channels
        #D0 = MUX_DATA
        #D1 = MUX_CLK
        #D2 = MUX_CLR
        #D3 = MUX1_nLE
        #D4 = MUX2_nLE
        #D5 = MUX3_nLE
        #D6 = MUX4_nLE

        mux_data_bits=144
        D0_MUX_DATA=np.zeros(mux_data_bits)        
        ##D1_MUX_CLK=np.zeros(dataLen)       
        D2_MUX_CLR=np.zeros(mux_data_bits)   
        D3_MUX1_nLE=np.ones(mux_data_bits)   
        D4_MUX2_nLE=np.ones(mux_data_bits)   
        D5_MUX3_nLE=np.ones(mux_data_bits)   
        D6_MUX4_nLE=np.ones(mux_data_bits)   
        
        ##Set CLR bits in D2_MUX_CLR
        D2_MUX_CLR[1]=1
        D2_MUX_CLR[0]=1
        
        
        if(tx_channel !=0 and rx_channel!=0 and tx_channel == rx_channel):
            if WARN_OUTPUT:
                print(
                    "Error setting new channels",
                    "- rx and tx must be different! No changes made.", sep='')
            return
        

        ##Add mapping table from transducer number to data bit number
        tx_data_bit=-1
        if(1<=tx_channel<=32):
            tx_data_bit=tx_channel+35
            self.tx_group = 1
        elif(32<tx_channel<=64):
            tx_data_bit=tx_channel+67
            self.tx_group = 2

        rx_data_bit=-1
        if(1<=rx_channel<=32):
            rx_data_bit=rx_channel+3
            self.rx_group = 1
        elif(32<rx_channel<=64):
            rx_data_bit=rx_channel+35   
            self.rx_group = 2
            
        #If tx_channel set to 0, then don't open any MUX channels for TX   
        #Use the tx_group with the SMA output    
        if(tx_channel==0):
             self.tx_group = 2
             tx_data_bit=0
        
        if(rx_channel==0):
            self.rx_group = 2
            rx_data_bit=0
            
            
        if DEV1_OUTPUT:
            print(
                "TX_channel: ",tx_channel,
                ", TX_data_bit: ",tx_data_bit,"\n",
                "RX_channel: ",rx_channel,
                ", RX_data_bit: ",rx_data_bit,                
                    sep='')        
        
       
       #Now select the multiplexer channels we want
        # Load latch data
        if DEV1_OUTPUT:
            print(
                "\nmatrix_controller::usm::set_multiplexer_channel, ",
                "setting rx, existing channel: ",
                str(self.rx_channel),
                ", existing group: ",
                str(self.rx_group), sep='')
        if rx_channel in range(
            multiplexer_1_transducers[0], multiplexer_1_transducers[1]
        ):
            self.rx_group = 1
            # store for future use
            self.rx_channel = rx_channel
        elif (rx_channel in range(
            multiplexer_2_transducers[0], multiplexer_2_transducers[1]
        )) or rx_channel==0:
            self.rx_group = 2
            # store for future use
            self.rx_channel = rx_channel
        if DEV1_OUTPUT:
            print(
                "new rx channel: ",
                str(self.rx_channel), ", new rx group: ",
                str(self.rx_group), sep='')

            


        # now do tx
        if DEV1_OUTPUT:
            print(
                "\nmatrix_controller::usm::set_multiplexer_channel, ",
                "setting tx, existing channel: ",
                str(self.tx_channel),
                ", existing group: ",
                str(self.tx_group), sep='')
            
            
        if (tx_channel in range(
            multiplexer_2_transducers[0], multiplexer_2_transducers[1]
        )) or tx_channel==0:
            

            # if we are changing tx group, we will need to change the 
            # trigger source for the analogue inputs, as well as the 
            # waveform generate output pin
            # the new group is 1 - check if that is not the same as the
            # existing
            if self.tx_group != 1:
                # channels are 0-indexed on the AD2
                dwf.FDwfAnalogOutNodeEnableSet(
                    self.device_handle, ctypes.c_int(0),
                    constants.AnalogOutNodeCarrier, ctypes.c_bool(True))
                dwf.FDwfAnalogInTriggerSourceSet(
                    self.device_handle, constants.trigsrcAnalogOut1)
            self.tx_group = 1
            # now store this new channel for future reference
            self.tx_channel = tx_channel
        elif tx_channel in range(
            multiplexer_1_transducers[0], multiplexer_1_transducers[1]
        ):
            # if we are changing tx group, we will need to change the 
            # trigger source for the analogue inputs, as well as the 
            # waveform generate output pin
            # the new group is 2 - check if that is not the same as the
            # existing
            if self.tx_group != 2:
                # channels are 0-indexed on the AD2
                dwf.FDwfAnalogOutNodeEnableSet(
                    self.device_handle, ctypes.c_int(1),
                    constants.AnalogOutNodeCarrier, ctypes.c_bool(True))
                dwf.FDwfAnalogInTriggerSourceSet(
                    self.device_handle, constants.trigsrcAnalogOut2)
            self.tx_group = 2
            # now store this new channel for future reference
            self.tx_channel = tx_channel
        if DEV1_OUTPUT:
            print(
                "new tx channel: ",
                str(self.tx_channel), ", new tx group: ",
                str(self.tx_group), sep='')

        #Set TX channel
        if(tx_data_bit!=0):
            D0_MUX_DATA[tx_data_bit]=1
               
        #Set RX channel
        if(rx_data_bit!=0):
            D0_MUX_DATA[rx_data_bit]=1

        
        #Set nLE position (set all to same position)
        D3_MUX1_nLE[131]=0
        D4_MUX2_nLE[131]=0
        D5_MUX3_nLE[131]=0
        D6_MUX4_nLE[131]=0
        
        ##Convert D0_MUX_DATA array into byte array
        # how many bytes we need to fit this many bits, (+7)/8
        D0_MUX_DATA_bytes=(ctypes.c_ubyte*((len(D0_MUX_DATA)+7)>>3))(0) 
       
        # array to bits in byte array
        for i in range(len(D0_MUX_DATA)):
            if D0_MUX_DATA[i] != 0:
                D0_MUX_DATA_bytes[i>>3] |= 1<<(i&7)

        ##Convert D2_MUX_CLR array into byte array
        D2_MUX_CLR_bytes=(ctypes.c_ubyte*((len(D2_MUX_CLR)+7)>>3))(0) 
        
        # array to bits in byte array
        for i in range(len(D2_MUX_CLR)):
            if D2_MUX_CLR[i] != 0:
                D2_MUX_CLR_bytes[i>>3] |= 1<<(i&7)                

        ##Convert D3_MUX1_nLE array into byte array
        D3_MUX1_nLE_bytes=(ctypes.c_ubyte*((len(D3_MUX1_nLE)+7)>>3))(0) 
        
        # array to bits in byte array
        for i in range(len(D3_MUX1_nLE)):
            if D3_MUX1_nLE[i] != 0:
                D3_MUX1_nLE_bytes[i>>3] |= 1<<(i&7)           

        ##Convert D4_MUX2_nLE array into byte array
        D4_MUX2_nLE_bytes=(ctypes.c_ubyte*((len(D4_MUX2_nLE)+7)>>3))(0) 
        
        # array to bits in byte array
        for i in range(len(D4_MUX2_nLE)):
            if D4_MUX2_nLE[i] != 0:
                D4_MUX2_nLE_bytes[i>>3] |= 1<<(i&7) 
                
        ##Convert D5_MUX3_nLE array into byte array
        D5_MUX3_nLE_bytes=(ctypes.c_ubyte*((len(D5_MUX3_nLE)+7)>>3))(0) 
        
        # array to bits in byte array
        for i in range(len(D5_MUX3_nLE)):
            if D5_MUX3_nLE[i] != 0:
                D5_MUX3_nLE_bytes[i>>3] |= 1<<(i&7) 
                
        ##Convert D6_MUX4_nLE array into byte array
        D6_MUX4_nLE_bytes=(ctypes.c_ubyte*((len(D6_MUX4_nLE)+7)>>3))(0) 
        
        # array to bits in byte array
        for i in range(len(D6_MUX4_nLE)):
            if D6_MUX4_nLE[i] != 0:
                D6_MUX4_nLE_bytes[i>>3] |= 1<<(i&7) 
        
        
        ##Set MUX data array (D0)
        dwf.FDwfDigitalOutDataSet(
            self.device_handle, ctypes.c_int(0),
            ctypes.byref(D0_MUX_DATA_bytes),
            ctypes.c_int(self.num_multiplexer_bus_message_bits))        
        
        ##Set CLR data array (D2)
        dwf.FDwfDigitalOutDataSet(
            self.device_handle, ctypes.c_int(2),
            ctypes.byref(D2_MUX_CLR_bytes),
            ctypes.c_int(self.num_multiplexer_bus_message_bits))           

        ##Set MUX1 data array (D3)
        dwf.FDwfDigitalOutDataSet(
            self.device_handle, ctypes.c_int(3),
            ctypes.byref(D3_MUX1_nLE_bytes),
            ctypes.c_int(self.num_multiplexer_bus_message_bits)) 

        ##Set MUX2 data array (D4)
        dwf.FDwfDigitalOutDataSet(
            self.device_handle, ctypes.c_int(4),
            ctypes.byref(D4_MUX2_nLE_bytes),
            ctypes.c_int(self.num_multiplexer_bus_message_bits)) 

        ##Set MUX3 data array (D5)
        dwf.FDwfDigitalOutDataSet(
            self.device_handle, ctypes.c_int(5),
            ctypes.byref(D5_MUX3_nLE_bytes),
            ctypes.c_int(self.num_multiplexer_bus_message_bits)) 

        ##Set MUX4 data array (D6)
        dwf.FDwfDigitalOutDataSet(
            self.device_handle, ctypes.c_int(6),
            ctypes.byref(D6_MUX4_nLE_bytes),
            ctypes.c_int(self.num_multiplexer_bus_message_bits))         

        # send the data
        # handle, start/stop
        dwf.FDwfDigitalOutConfigure(
            self.device_handle, ctypes.c_int(1))

    def set_custom_waveform(self, wavegen_samples):
        num_samples = len(wavegen_samples)
        if(self.num_wavegen_samples <= self.max_num_wavegen_samples):
            self.num_wavegen_samples = num_samples
            self.wavegen_samples = (
                ctypes.c_double * num_samples)(*wavegen_samples)
        
        elif ERROR_OUTPUT:
            print(
                "\nmatrix_controller::::usm::init, ",
                "Too many waveform samples! ",
                "Number provided: ", str(self.num_wavegen_samples))
        
        if DEV1_OUTPUT:
            print(
                "\nmatrix_controller::::usm::set_custom_waveform",
                "\nnew num wavegen samples: ",
                str(self.num_wavegen_samples), sep='')
        # TMI
#        if DEV2_OUTPUT:
#            print(
#                "\nNew wavegen samples: ", list(self.wavegen_samples))
    
    def config_wavegen(
        self, abs_drive_v, drive_shape, drive_frequency, num_drive_cycles):
        self.abs_drive_v = abs_drive_v
        self.drive_shape = drive_shape
        self.num_drive_cycles = num_drive_cycles
        self.drive_frequency = drive_frequency
        self.drive_time_s = self.num_drive_cycles / self.drive_frequency

    def acquire_measurement(self):
        if (
            self.device_handle.value > 0
            and self.tx_group > 0
            and self.rx_group > 0
        ):
            if DEV1_OUTPUT:
                print(
                    "\nmatrix_controller::acquire_measurement, "
                    "starting measurement", sep='')
            # don't reconfigure, start oscilloscope instrument
            dwf.FDwfAnalogInConfigure(
                self.device_handle, ctypes.c_bool(False),
                ctypes.c_bool(True))
            
            if self.drive_shape == "square":
                dwf.FDwfAnalogOutNodeFunctionSet(
                    self.device_handle, ctypes.c_int(-1),
                    constants.AnalogOutNodeCarrier, constants.funcSquare)
            elif self.drive_shape == "sine":
                dwf.FDwfAnalogOutNodeFunctionSet(
                    self.device_handle, ctypes.c_int(-1),
                    constants.AnalogOutNodeCarrier, constants.funcSine)
            elif self.drive_shape == "custom":
                dwf.FDwfAnalogOutNodeFunctionSet(
                    self.device_handle, ctypes.c_int(-1),
                    constants.AnalogOutNodeCarrier, constants.funcCustom)
                dwf.FDwfAnalogOutNodeDataSet(
                    self.device_handle, ctypes.c_int(-1),
                    constants.AnalogOutNodeCarrier, self.wavegen_samples,
                    ctypes.c_int(self.num_wavegen_samples))
            dwf.FDwfAnalogOutNodeFrequencySet(
                self.device_handle, ctypes.c_int(-1),
                constants.AnalogOutNodeCarrier,
                ctypes.c_double(self.drive_frequency))
            dwf.FDwfAnalogOutNodeAmplitudeSet(
                self.device_handle,
                ctypes.c_int(-1), constants.AnalogOutNodeCarrier,
                ctypes.c_double(self.abs_drive_v))
            dwf.FDwfAnalogOutNodeOffsetSet(
                self.device_handle, ctypes.c_int(-1),
                constants.AnalogOutNodeCarrier, ctypes.c_double(0))
            dwf.FDwfAnalogOutIdleSet(
                self.device_handle, ctypes.c_int(-1),
                constants.DwfAnalogOutIdleOffset)
            dwf.FDwfAnalogOutRunSet(
                self.device_handle, ctypes.c_int(-1),
                ctypes.c_double(self.drive_time_s)) 
            # wait time after being triggered to start output
            dwf.FDwfAnalogOutWaitSet(
                self.device_handle, ctypes.c_int(-1), ctypes.c_double(0))
            # repeat value for generated signal
            dwf.FDwfAnalogOutRepeatSet(
                self.device_handle, ctypes.c_int(-1), ctypes.c_int(1))

            # configure and turn on waveform generator
            dwf.FDwfAnalogOutConfigure(
                self.device_handle, ctypes.c_int(-1),
                ctypes.c_bool(True))
                            
            # Start capturing samples in blocking mode (necessary because
            # we are recording more samples than the buffer size)
            status = ctypes.c_byte()
            ch1_samples = (ctypes.c_double*self.acq_num_samples.value)()
            ch2_samples = (ctypes.c_double*self.acq_num_samples.value)()
            num_avail_samples = ctypes.c_int()
            num_lost_samples = ctypes.c_int()
            num_corrupted_samples = ctypes.c_int()
            flag_samples_lost = 0
            flag_samples_corrupted = 0
            
            capture_buffer_index = 0
            while True:
                dwf.FDwfAnalogInStatus(
                    self.device_handle, ctypes.c_int(1), ctypes.byref(status))
                dwf.FDwfAnalogInStatusRecord(
                    self.device_handle, ctypes.byref(num_avail_samples),
                    ctypes.byref(num_lost_samples),
                    ctypes.byref(num_corrupted_samples))
                if DEV2_OUTPUT:
                    print(
                        "\n capture_buffer_index: ",
                        str(capture_buffer_index),
                        ", AIN status: ", str(status.value),
                        ", num. available: ", str(num_avail_samples.value),
                        sep='')
                capture_buffer_index += num_lost_samples.value
                capture_buffer_index %= self.acq_num_samples.value

                if num_lost_samples.value:
                    flag_samples_lost = 1
                if num_corrupted_samples.value:
                    flag_samples_corrupted = 1

                acq_sample_index = 0
                while num_avail_samples.value > 0:
                    num_samples_acq = num_avail_samples.value
                    # we are using circular sample buffer
                    # make sure to not overflow
                    if (
                        capture_buffer_index + num_avail_samples.value
                        > self.acq_num_samples.value
                    ):
                        # only fill to end of buffer
                        num_samples_acq = (
                            self.acq_num_samples.value
                            - capture_buffer_index)
                    # get channel 1 data
                    dwf.FDwfAnalogInStatusData2(
                        self.device_handle,
                        ctypes.c_int(0),
                        ctypes.byref(
                            ch1_samples,
                            (ctypes.sizeof(ctypes.c_double)
                                * capture_buffer_index)),
                        ctypes.c_int(acq_sample_index),
                        ctypes.c_int(num_samples_acq))
                    
                    # get channel 2 data
                    dwf.FDwfAnalogInStatusData2(
                        self.device_handle,
                        ctypes.c_int(1),
                        ctypes.byref(
                            ch2_samples,
                            (ctypes.sizeof(ctypes.c_double)
                            * capture_buffer_index)),
                        ctypes.c_int(acq_sample_index),
                        ctypes.c_int(num_samples_acq))

                    acq_sample_index += num_samples_acq
                    num_avail_samples.value -= num_samples_acq
                    # advance circular buffer index
                    capture_buffer_index += num_samples_acq
                    capture_buffer_index %= self.acq_num_samples.value

                if status.value == 2 : # done
                    break

            if capture_buffer_index != 0:
                # de-circularise
                ch1_samples = (ch1_samples[capture_buffer_index:]
                    + ch1_samples[:capture_buffer_index])
                ch2_samples = (ch2_samples[capture_buffer_index:]
                    + ch2_samples[:capture_buffer_index])

            if ERROR_OUTPUT and flag_samples_lost:
                print("Samples were lost! Reduce frequency")
            if ERROR_OUTPUT and flag_samples_corrupted:
                print("Samples could be corrupted! Reduce frequency")
            header1 = ["tx_channel", "rx_channel", "abs_drive_v",
                "drive_shape", "set_max_meas_voltage_vpp", "trigger_v",
                "trigger_time_s", "drive_frequency", "num_drive_cycles",
                "sample_rate", "acq_time_ms"]
            header2 = [str(self.tx_channel), str(self.rx_channel),
                str(self.abs_drive_v), str(self.drive_shape), 
                str(self.max_meas_voltage_vpp), str(self.trigger_v),
                str(self.trigger_time_s), str(self.drive_frequency),
                str(self.num_drive_cycles), str(self.sample_rate),
                str(self.acq_time_ms)]
            retVal = 0
            if self.rx_group == 1:
                ch1_samples.insert(0, header1)
                ch1_samples.insert(1, header2)
                retVal = list(ch1_samples)
            elif self.rx_group == 2:
                ch2_samples.insert(0, header1)
                ch2_samples.insert(1, header2)
                retVal = list(ch2_samples)
            return retVal

    def close(self):
        if self.device_handle.value > 0:
            dwf.FDwfAnalogOutReset(
                self.device_handle, ctypes.c_int(-1)) # reset all channels
            dwf.FDwfDeviceCloseAll()
