# Translate Stage

A Python script for automated translation of the Zaber linear stage. Written and tested using the X-LSM200A-E03 stage in the UNDT lab.

## Setup

To get started, a Python installation with `zaber-motion` and `pyserial` packages is required. Suggested to set up a new environment using `mamba`:
- Install [`mamba-forge`](https://github.com/conda-forge/miniforge#mambaforge) to your device.
- Create a new environment from the Miniforge Prompt: `mamba create -n translate_stage pyserial`  
List additional desired packages at the end of the command (e.g. `numpy`, `scipy`, `matplotlib`, `spyder`).
- Activate the environment: `mamba activate translate_stage
- Install the `zaber-motion` package: `python -m pip install --user zaber-motion`

You may need to install the correct drivers to connect to the Zaber linear stage: see the [USB drivers](https://www.zaber.com/software) page to install.

Clone this repo to your own device: navigate to the desired parent directory and use `git clone https://github.com/mgchandler/translate_stage.git` to download the repo. When an update is made available, use `git pull` to pull the latest version to your device.

## To do list:

- [ ] Figure out how to move more than one device at a time. End goal: trace out diagonals and circles.  
	- [ ] Use streams to do this? Store actions to the buffer and then stream them. Try triggers to start motion when desired.
- [ ] Build in offline usage  
      (Function `zaber_motion.Library.enable_device_db_store()` updates local devices from internet. Want to have this behaviour by default, but fall back to local database if not connected / found).
- [ ] Translate the stage along a predefined path (supplied by `yaml`?)  
      Enables use of feedback loop to return to likely defect site.
- [ ] Get to a point where the script can be run from the command line only - no additional scripting required.
- [ ] GUI?