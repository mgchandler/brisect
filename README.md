# ECT Smart Scan

A Python library for automated scanning of a metallic component using eddy current coil. 2D scanning using Zaber linear stages enabled using feedback from measurements made by a Handyscope.
Written and tested using X-LSM200A-E03 linear stages in x- and y-axes in the UNDT lab, with Handyscope HS5 making measurements.

## Setup

To get started, a Python installation with `zaber-motion` and `pyserial` packages is required. Suggested to set up a new environment using `mamba`:
- Install [`mamba-forge`](https://github.com/conda-forge/miniforge#mambaforge) to your device.
- Create a new environment from the Miniforge Prompt: `mamba create -n translate_stage pyserial`  
List additional desired packages at the end of the command (e.g. `numpy`, `scipy`, `matplotlib`, `spyder`).
- Activate the environment: `mamba activate translate_stage
- Install the `zaber-motion` package: `python -m pip install --user zaber-motion`
- Install the `libtiepie` package: `python -m pip install python-libtiepie`

You may need to install the correct drivers to connect to the Zaber linear stage: see the [USB drivers](https://www.zaber.com/software) page to install.

Make a fork of this repo on GitHub, and clone it to your device. Make changes there, and then make a pull request when significant changes made.

## To do list:

- Zaber motion package:
	- [x] Investigate how to move two devices at once, and make complex trajectory using both.
		- [x] move_relative() fns take velocity arguments in v7 - cannot update beyond v6.
		- [x] Manually reproduce move_relative using `axis.settings.set("maxspeed", velocity)` for each axis and then do the movement.
		- [ ] Look at streaming to reduce stop/start motion when making arcs.
		- [ ] Investigate triggers to adjust speed to make arcs.
	- [ ] Specify trajectory using external definition (e.g. `yaml` file?)
	- [ ] Offline usage (function `zaber_motion.Library.enable_device_db_store()` updates from internet - need alternative behaviour when not available).
- Handyscope package:
	- [ ] Read in magnitude and phase data.
	- [ ] Process input data to meaningful form.
- Feedback loop for detection:
	- [ ] Determine geometry of the part being inspected.
		- [ ] Coarse scan of entire domain with zaber.
		- [ ] In first instance, fit a box to metallic region.
		- [ ] More clever prediction of geometry from resulting map.
	- [ ] Coarse scan of part for defects.
		- [ ] Similar scanning of part domain.
		- [ ] Look for deviations from pristine material.
		- [ ] Identify a way to return to these regions for a more fine scan
- Miscellaneous:
	- [ ] Run program from command line, return all useful analysis as plots or print to screen.
	- [ ] GUI?