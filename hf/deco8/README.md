
Decomposition of a 3D Interferogram Using a Basis Set of 2D Interferograms.
The demo uses some recently-modified components of NMRPipe, so it won't 
work on all systems yet.

frank.delaglio@nist.gov 5/2024

all.com
 The script that does the decomposition independently for each 2D plane of the input
 input 3D interferogram, both with and without a non-uniform sampling (NUS) mask.
 The script uses the "deco2D.tcl" NMRPipe utility.

clean.com
 A script to delete previous results.

sim_ft1/test%03d.ft1
 The input 3D interferogram in 2D plane format.

mask_ft1/test%03d.ft1
 The corresponding input 3D mask in 2D plane format.

basis_ft1/*.ft1
 The basis set of 100 2D interferograms.

sim.ft1
 The 3D single-file version of input sim_ft1/test%03d.ft1

mask.ft1
 The 3D single-file version of input mask_ft1/test%03d.ft1

simNUS_ft1
 The input 3D NUS interferogram in 2D plane format. The NUS
 interferogram is the original 3D interferogram times the mask.

synth_ft1/test%03d.ft1
 The output decomposition of sim_ft1/test%03d.ft1 using basis basis_ft1/*.ft1

synth.ft1
 The 3D single-file version of output synth_ft1/test%03d.ft1

synthNUS_ft1/test%03d.ft1
 The output decomposition of simNUS_ft1/test%03d.ft1 using basis basis_ft1/*.ft1
 and mask mask/test%03d.fid

synthNUS.ft1
 The 3D single-file version of output synthNUS_ft1/test%03d.ft1

pypeDeco.com
 Comparison of decompositions by nmrPype and deco2D.tcl. The current output shown below.
 According to the output, decomposition of 2D interferogram works, 3D interferogram doesn't
 work, and both the 2D and 3D cases using a mask don't work:

   Decomposition Tests: all difPct values should be much less than one.

   3D Decomposition by nmrPype, with and without NUS mask:
   sim.ft1 -2.795835e-01 2.231860e-01 873600 pype_synth.ft1 -8.831234e-02 1.124180e-01 873600 dif -2.334197e-01 1.842562e-01 873600 difPct 83.488368 264.31153
   simNUS.ft1 -3.619758e-01 4.334339e-01 873600 pype_synthNUS.ft1 -8.831234e-02 1.124180e-01 873600 dif -3.044222e-01 3.634444e-01 873600 difPct 84.100153 344.71083

   2D Decomposition of a selected plane by nmrPype, with and without NUS mask:
   sim_test010.ft1 -1.920722e-01 1.626231e-01 8736 pype_synth_010.ft1 -1.920425e-01 1.626305e-01 8736 dif -4.730260e-05 6.058145e-05 8736 difPct 0.037252672 0.037250977
   simNUS_test010.ft1 -1.228966e-01 1.277565e-01 8736 pype_synthNUS_010.ft1 -4.506085e-02 4.596171e-02 8736 dif -9.807683e-02 1.025692e-01 8736 difPct 80.284917 223.16228

   2D Decomposition of the same plane by deco2D.tcl, with and without NUS mask:
   sim_ft1/test010.ft1 -1.920722e-01 1.626231e-01 8736 synth_010.ft1 -1.920439e-01 1.626318e-01 8736 dif -4.731707e-05 6.058202e-05 8736 difPct 0.037253022 0.03725103
   simNUS_ft1/test010.ft1 -1.228966e-01 1.277565e-01 8736 synthNUS_010.ft1 -1.228943e-01 1.277519e-01 8736 dif -4.625156e-05 6.057160e-05 8736 difPct 0.047411756 0.047413463
 
