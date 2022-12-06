## Translate Stage

A Python library for automated translation of the Zaber linear stage. Written and tested using the X-LSM200A-E03 stage in the UNDT lab.

# Setup

To get started, a Python installation with `zaber-motion` and `pyserial` packages is required. Suggested to set up a new environment using `mamba`:
- Install [`mamba-forge`](https://github.com/conda-forge/miniforge#mambaforge) to your device.
- Create a new environment from the Miniforge Prompt:  
`mamba create -n translate_stage pyserial`  
List additional desired packages at the end of the command (e.g. `numpy`, `scipy`, `matplotlib`, `spyder`).
- Activate the environment:  
`mamba activate translate_stage
- Install the `zaber-motion` package:  
`python -m pip install --user zaber-motion`

You may need to install the correct drivers to connect to the Zaber linear stage: see the [USB drivers](https://www.zaber.com/software) page to install.

Clone this repo to your own device: navigate to the desired parent directory and use  
`git clone https://github.com/mgchandler/translate_stage.git`  
to download the repo. When an update is made available, use `git pull` to pull the latest version to your device.