# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 12:40:48 2023

@author: mc16535
"""

"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
From https://github.com/pypa/sampleproject/blob/master/setup.py
"""

from setuptools import setup, find_packages, Extension

import codecs
import re
import os
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


# --- Begin snippet from https://github.com/pypa/pip/blob/1.5.6/setup.py#L33
def read(*parts):
    # intentionally *not* adding an encoding option to open
    # see here: https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), "r").read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# --- End snippet

setup(
    name="brisect",
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=find_version("brisect", "__init__.py"),
    description="Python library to improve working with handyscopes and translation stages",
    long_description=long_description,
    url="https://github.com/mgchandler/brisect",
    author="Matt Chandler, Alexis Hernandez Arroyo",
    author_email="m.chandler@bristol.ac.uk",
    # Choose your license
    license="License :: OSI Approved :: MIT License",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        # Pick your license as you wish (should match "license" above)
        # 'License :: OSI Approved :: MIT License',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    # What does your project relate to?
    keywords="bristol, ect, undt, handyscope, translation, stage, scan",
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=["driver", "driver.*", "useful_templates", "useful_templates.*", "docs", "tests", "tests.*"]),
    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=["numpy", "scipy", "matplotlib", "pyyaml", "pyserial", "python-libtiepie", "zaber-motion"],
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        "dev": ["pytest", "numdifftools", "sphinx", "sphinx_rtd_theme", "black"]
    },
    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        "default_settings": ["*.yml"]
    },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={"console_scripts": ["arim = arim.cli:main"]},
    # ext_modules=[],
    zip_safe=False,
)