# Note: if pip is not installed, try to bootstrap using:
#   python -m ensurepip --default-pip
# Or download https://bootstrap.pypa.io/get-pip.py
#
# Then install setuptools:
# python -m pip install --upgrade pip setuptools wheel
from setuptools import (setup, find_packages)

exec(open('hdlmake/_version.py').read())

try:
    __version__
except Exception:
    __version__ = "0.0"  # default if for some reason the exec did not work

setup(
   name="hdlmake",
   version=__version__,
   description="Hdlmake generates multi-purpose makefiles for HDL projects management.",
   author="Javier D. Garcia-Lasheras",
   author_email="hdl-make@ohwr.org",
   license="GPLv3",
   url="http://www.ohwr.org/projects/hdl-make",
   packages=find_packages(),
   entry_points={
      'console_scripts': [
         'hdlmake = hdlmake.main:main',
         ], 
   },
   include_package_data=True,  # use MANIFEST.in during install
   classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Environment :: Console",
      "Topic :: Utilities",
      "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
      "Topic :: Software Development :: Build Tools",
    ],
   )
