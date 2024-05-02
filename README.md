# nmrPype
Python implementation of command-line program nmrpipe, using linux pipelines to process NMR data.

- **Documentation:** https://phimykah.github.io/nmrpype
- **NMRPipe Website:** https://www.ibbr.umd.edu/nmrpipe
- **Source Code:** https://github.com/PhiMykah/nmrPype
- **Bug Reports:** https://github.com/PhiMykah/nmrPype/issues

Installation
============
Installing nmrPype can be done by through pip:
```sh
# Install prerequisites
pip install numpy scipy
# Install program
pip install nmrPype
``` 
A virtual environment or conda environment is recommended for using nmrPype.
If using conda, `numpy` and `scipy` can be installed using `conda install`.

### Note

This is made for Python 3.10 or above. Some of the code requires Python 3.10's features such as `match-case` statements. 

Python 3.12 is recommended as development is done with 3.12, but testing is done to assure that 3.10 is supported.

Usage
==========
nmrPype can be used in through two methods: Command-line and Script

Command-line
--------------
```
nmrPype -in [inFile] -fn fnName -out [outFile] [-ov]
```
Functions:
```
FT                  Perform a Fourier transform (FT) on the data
ZF                  Perform a Zero Fill (ZF) Operation on the data
SP (SINE)           Adjustable Sine Bell
PS                  Perform a Phase Correction (PS) on the data
YTP (TP, XY2YX)     2D Plane Transpose
ZTP (XYZ2ZYX)       3D Matrix Transpose
ATP (XYZA2AYZX)     4D Matrix Transpose (unimplemented)
NULL                Null Function, does not apply any function
```
Run the `nmrPype --help` command to see a list of more options.

Script
------
In a Python script or jupyter notebook use the following line:
```py
import nmrPype
```
I recommend setting the import as `pype` for simplification.
### Example
```py
import nmrPype as pype

df = pype.DataFrame("h.fid") # Load NMR data file into script
df.array() # Display spectral data array
```

Building From Source
====================

### Building using Pip

1. Install prerequisites
```sh
pip install numpy scipy
```
2. Clone the repository
```sh
git clone https://github.com/PhiMykah/nmrPype
```
3. Install in development mode with pip:

```sh
cd nmrPype
pip install -e .
```

### Building using Conda

With conda, the environment.yml file can be used to obtain
the development environment.

1. Clone the repository
```sh
git clone https://github.com/PhiMykah/nmrPype
```
2. Copy the source conda environment
```sh
cd nmrPype
conda env create -f environment.yml --name nmrpype
```
- You can set the name to anything you wish, but typically
my convention is to have the environments lowercase

3. Install in development mode with pip:
```
pip install -e .
```

