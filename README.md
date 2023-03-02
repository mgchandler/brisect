# Bris-ECT

A Python library for standardisation of Handyscope and translation stages. This has currently been tested with handyscopes HS3 and HS5, and with Zaber linear stages (X-LSM200A-E03) which have firmware v6. Minor changes will need to be made regarding the velocity of stages if firmware v7 is used.
Tested with Handyscope drivers v8.1.9. Developed with Python v3.10.

## Setup

To get started, a valid Python installation is required. We advise that you create a new environment to install brisect to.

- Install [`mamba-forge`](https://github.com/conda-forge/miniforge#mambaforge) to your device.
- Create a new environment from the Miniforge Prompt: `mamba create -n bris-ect`
- Activate the environment: `mamba activate bris-ect`
- [Download](https://github.com/mgchandler/brisect/blob/main/dist/brisect-0.1.2a1-py3-none-any.whl) the `brisect-x.x-py3-non-any.whl` file to a location on your device - note that the file you download will have a release version rather than `x.x`.
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
	- [x] Investigate how to make two devices move at once. Make a complicated trajectory using both.
		- [x] Write equivalent for `move_relative(x, v)` function. In firmware >= v7 it takes velocity, in v6 it doesn't.
			- Wrapper function sets velocity first, then moves. On shutdown, reset the velocity to original.
		- [ ] Work out if streaming is feasible to reduce stop/start jerky motion when drawing out arcs.
			- Not a priority as we can just move with right angles right now. Shelf it for now.
	- [x] Feed in a trajectory from external file.
		- [x] Use `yaml` to do it.
		- (01/03/23) `ect-smart-scan.py` is now trying to work it out smartly - don't need to feed in trajectory externally.
		- [ ] Make an example script which moves along an arbitrary path which is provided externally.
	- [ ] Offline usage (function `zaber_motion.Library.enable_device_db_store()` updates from the internet. Alternative behaviour if offline.)
	
- Handyscope package:
	- [x] Work out why Python cannot communicate with Handyscopes
		- Current `python-libtiepie` version does not work with most recent drivers - use v8.1.9
	- [ ] Acquire magnitude and phase when processing.
	- [x] Read in data in real time (or as close as possible).
	- [x] Pass in and measure arbitrary signals.
		- [x] Multiplexed signals have default behaviour.
		- [x] Method in Handyscope class to write any arbitrary signal. This is also accessible from `Handyscope.gen.set_data()`.
			- May automate chirps and bandwidths later.
	- [ ] Processing output data to meaningful form.
		- [x] RMS, frequency spectrum data.
- Feedback loop (`ect-smart-scan.py`):
	- [x] Determine geometry of the part being inspected.
		- [x] Coarse scan of entire domain with zaber.
		- [x] In first instance, fit a box to metallic region.
		- [ ] More clever prediction of geometry from resulting map.
		  - [x] Snake around the full space until geometry found. At which point trace the edges of the geometry.
		  - [x] Trace the geometry: move back and forth over edge of geometry until a corner found. Use value of RMS to determine whether to turn left or right, and scan the next edge. Detect when the probe has returned to the start position.
	- [x] Coarse scan of part for defects.
		- [x] Look for deviations from pristine material.
			- Can implement by reusing the sweep for the geometry.
			- When scanning off and on the part, work out whether we are closer to one RMS or the other (i.e. vacuum vs part).
	- [x] For RMS voltage: correct for vertical liftoff of probe.
		- [x] In first instance treat it as linear `V = ax + by + c`
		- [ ] Are there any non-linear effects in liftoff? May need to add other effects.
		- Decision to move away from liftoff correction in post processing. Will instead try to correct mechanically with spring pushing coil down, and levelling the part as much as possible.
	- [ ] For phase: compare phase difference of input signal to output signal.
		- [x] Check how good our generated input signal is, vs channel measurement on handyscope
			- Signal looks very good, small amount of noise but not awful.  
			  There is a phase difference from the generation depending on when generator started and stopped - will be necessary to measure the generated signal on the handyscope to compare to the output from the coil.
- Miscellaneous:
	- [x] Select a more appropriate capacitor.
	- [x] Select a more appropriate frequency.
	- [x] Run program from command line, return all useful analysis as plots or print to screen.
	- [ ] GUI?
		- What would be needed from a GUI? All the inputs, plus a window for where the scan goes?