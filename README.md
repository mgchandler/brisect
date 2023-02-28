# Bris-ECT

A Python library for standardisation of Handyscope and translation stages. This has currently been tested with handyscopes HS3 and HS5, and with Zaber linear stages (X-LSM200A-E03) which have firmware v6. Minor changes will need to be made regarding the velocity of stages if firmware v7 is used.
Tested with Handyscope drivers v8.1.9. Developed with Python v3.10.

## Setup

To get started, a valid Python installation is required. We advise that you create a new environment to install brisect to.

- Install [`mamba-forge`](https://github.com/conda-forge/miniforge#mambaforge) to your device.
- Create a new environment from the Miniforge Prompt: `mamba create -n bris-ect`
- Activate the environment: `mamba activate bris-ect`
- [Download](https://github.com/mgchandler/brisect/releases/download/v0.1a1/brisect-0.1a1-py3-none-any.whl) the `brisect-x.x-py3-non-any.whl` file to a location on your device - note that the file you download will have a release version rather than `x.x`.
- In the Miniforge console, change to the directory in which you saved the `*.whl` file.
- Install the file: `python -m pip install brisect-x.x-py3-non-any.whl`. Change `x.x` to the version number you downloaded.

Note that you may wish to install an IDE as well: `brisect` has been developed with Spyder (`mamba install spyder`). Others exist but your mileage may vary.

You may need to install the correct drivers to connect to the Zaber linear stage: see the [USB drivers](https://www.zaber.com/software) page to install. TiePie driver v10 doesn't work with `python-libtiepie`, use v8.1.9 instead. An .exe is available in `.\drivers`.

If you are developing changes to this package, make a fork of this repo on GitHub, and clone it to your device. Make changes there, and then make a pull request when significant changes are made.

## Usage

See the `examples` folder for examples of how to use this package. If you have any problems or wish to request / add new features, please raise an issue on GitHub.

`examples\ect-smart-scan.py` can either be run from an IDE or from the command line. To use from the command line, make a custom `<filename>.yml` file with properties filled out as found in the example in this repo.  
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