"""
Submodule of brisect which contains a Python wrapper for the Handyscope.

Classes:
    Handyscope:
        Methods:
            new_params
            get_record
        Class Methods:
            from_yaml
        Attributes:
            gen
            scp

Variables:
    gen_dict
    scp_dict
    mode_dict
"""

from .handyscope import *