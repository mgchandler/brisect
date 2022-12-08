# Translate Stage

A Python script for automated translation of the Zaber linear stage. Written and tested using the X-LSM200A-E03 stage in the UNDT lab.

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

- [ ] Figure out how to move more than one device at a time. End goal: trace out diagonals and circles. 
	- [x] Investigate streams to do this. May need to update firmware as some functions introduced in v7. x- and y-axes currently on v6.19, z-axis on 7.8.
	- [x] Firmware update not possible: devices cannot be updated outside of their major version. Setting `maxspeed` via composite move_rel_v() and move_abs_v() functions works on stage on v6.28 - need to test circle tracing on double stage.
	- [ ] Investigate a way to activate several streams at one time, or at least activate with minimal delay. Look at triggers to do this.
	- [ ] For arc: consider moving it from start to end, and use triggers to change the speed
- [ ] Translate the stage along a predefined path (supplied by `yaml`?)  
- [ ] Build in offline usage  
      (Function `zaber_motion.Library.enable_device_db_store()` updates local devices from internet. Want to have this behaviour by default, but fall back to local database if not connected / found).
      Enables use of feedback loop to return to likely defect site.
- [ ] Get to a point where the script can be run from the command line only - no additional scripting required.
- [ ] Feedback loop from coil output
- [ ] GUI?