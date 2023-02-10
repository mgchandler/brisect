# ECT Smart Scan

A Python library for automated scanning of a metallic component using eddy current coil. 2D scanning using Zaber linear stages enabled using feedback from measurements made by a Handyscope.
Written and tested using X-LSM200A-E03 linear stages in x- and y-axes in the UNDT lab, with Handyscope HS5 making measurements, with drivers v8.1.9. Developed with Python v3.10.

## Setup

To get started, a Python installation with `zaber-motion` and `python-libtiepie` packages is required. Suggested to set up a new environment using `mamba`:
- Install [`mamba-forge`](https://github.com/conda-forge/miniforge#mambaforge) to your device.
- Create a new environment from the Miniforge Prompt: `mamba create -n ect-smart-scan matplotlib numpy pyserial scipy spyder yaml` 
- Activate the environment: `mamba activate ect-smart-scan`  
- Install the `zaber-motion` package: `python -m pip install zaber-motion`
- Install the `libtiepie` package: `python -m pip install python-libtiepie`

You may need to install the correct drivers to connect to the Zaber linear stage: see the [USB drivers](https://www.zaber.com/software) page to install. TiePie driver v10 doesn't work with `python-libtiepie`, use v8.1.9 instead.

Make a fork of this repo on GitHub, and clone it to your device. Make changes there, and then make a pull request when significant changes made.

## Usage

`ect-smart-scan.py` can either be run from an IDE or from the command line. To use from the command line, make a custom `<filename>.yml` file with properties filled out as found in the example in this repo.  
To run from an IDE, the `yaml_filename` variable on line 33 must be changed. To run from the command line, make sure that the `mamba` environment is activated and run `python ect-smart-scan.py <filename>.yml`. The script will execute, saving a png of the measured RMS values in the `output` directory.

## To do list:

- Zaber motion package:
	- [x] Investigate how to move two devices at once, and make complex trajectory using both.
		- [x] `move_relative()` fns take velocity arguments in v7 - cannot update beyond v6.
		- [x] Manually reproduce move_relative using `axis.settings.set("maxspeed", velocity)` for each axis and then do the movement.
		- [ ] Look at streaming to reduce stop/start motion when making arcs.
			- Arc behaviour not entirely required but would be nice down the line.
		- [ ] Investigate triggers to adjust speed to make arcs.
	- [x] Specify trajectory using external definition (e.g. `yaml` file?)
	- [ ] Offline usage (function `zaber_motion.Library.enable_device_db_store()` updates from internet - need alternative behaviour when not available).
- Handyscope package:
	- [x] Work out why Python cannot communicate with Handyscopes
		- Current `python-libtiepie` version does not work with most recent drivers - use v8.1.9
	- [ ] Read in magnitude and phase data.
		- [x] Read in data in real time as well!
	- [x] Pass in and measure arbitrary signals.
		- Currently, multiplexed signals of N single frequencies with different amplitudes supported.
		- Bands and chirps would be of interest in the future, but not currently implemented.
	- [x] Process input data to meaningful form.
- Feedback loop for detection:
	- [x] Determine geometry of the part being inspected.
		- [x] Coarse scan of entire domain with zaber.
		- [x] In first instance, fit a box to metallic region.
		- [ ] More clever prediction of geometry from resulting map.
		  - [x] Snake around the full space until geometry found. At which point trace the edges of the geometry.
		  - [ ] Trace the geometry: move back and forth over edge of geometry until a corner found. Use value of RMS to determine whether to turn left or right, and scan the next edge. Detect when the probe has returned to the start position.
	- [x] Coarse scan of part for defects.
		- [ ] Look for deviations from pristine material.
		- [ ] Identify a way to return to these regions for a more fine scan
	- [x] For RMS voltage: correct for vertical liftoff of probe.
		- [x] In first instance treat it as linear `V = ax + by + c`
		- [ ] Are there any non-linear effects in liftoff? May need to add other effects.
	- [ ] For phase: compare phase difference of input signal to output signal.
		- [x] Check how good our generated input signal is, vs channel measurement on handyscope
			- Signal looks very good, small amount of noise but not awful.  
			  There is a phase difference from the generation depending on when generator started and stopped - will be necessary to measure the generated signal on the handyscope to compare to the output from the coil.
- Miscellaneous:
	- [x] Select a more appropriate capacitor.
	- [x] Select a more appropriate frequency.
	- [x] Run program from command line, return all useful analysis as plots or print to screen.
	- [ ] GUI?