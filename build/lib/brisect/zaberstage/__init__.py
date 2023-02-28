"""
Submodule of brisect which contains a Python wrapper for the zaber-motion 
translation stage. This is written with a standardised format, making it easier
to use the scripts developed with this `Stage` class with other translation
stages: simply import the wrapper for the alternative stage instead (if one
exists - wrappers may need to be written for new devices).

Classes:
    Stage:
        Methods:
            move
            stop
            shutdown
            get_position
        Attributes:
            connection
            axes
            mm_resolution
"""

from .stage import *