#!/bin/csh

echo "Decomposition Tests: all difPct values should be much less than one."
echo ""

echo "3D Decomposition by nmrPype, with and without NUS mask:"

nmrPype -in sim.ft1    -fn DECO -basis basis_ft1/*.ft1 -cfile coef.dat                -out pype_synth.ft1    -ov
nmrPype -in simNUS.ft1 -fn DECO -basis basis_ft1/*.ft1 -cfile coef.dat -mask mask.ft1 -out pype_synthNUS.ft1 -ov

showDif.com -in1 sim.ft1    -in2 pype_synth.ft1
showDif.com -in1 simNUS.ft1 -in2 pype_synthNUS.ft1


echo ""
echo "2D Decomposition of a selected plane by nmrPype, with and without NUS mask:"

/bin/cp sim_ft1/test010.ft1    sim_test010.ft1
/bin/cp simNUS_ft1/test010.ft1 simNUS_test010.ft1
/bin/cp mask_ft1/test010.ft1   mask_test010.ft1

#
# Currently, nmrPype can't use a 2D plane from a 3D as output, set header to 2D:

sethdr sim_test010.ft1    -ndim 2
sethdr simNUS_test010.ft1 -ndim 2
sethdr mask_test010.ft1   -ndim 2

nmrPype -in sim_test010.ft1    -fn DECO -basis basis_ft1/*.ft1 -cfile coef.dat                        -out pype_synth_010.ft1    -ov
nmrPype -in simNUS_test010.ft1 -fn DECO -basis basis_ft1/*.ft1 -cfile coef.dat -mask mask_test010.ft1 -out pype_synthNUS_010.ft1 -ov

showDif.com -in1 sim_test010.ft1    -in2 pype_synth_010.ft1
showDif.com -in1 simNUS_test010.ft1 -in2 pype_synthNUS_010.ft1

echo ""
echo "2D Decomposition of the same plane by deco2D.tcl, with and without NUS mask:"

deco2D.tcl -noverb -in sim_ft1/test010.ft1    -basis basis_ft1/*.ft1 -out synth_010.ft1
deco2D.tcl -noverb -in simNUS_ft1/test010.ft1 -basis basis_ft1/*.ft1 -out synthNUS_010.ft1 -mask mask_test010.ft1

showDif.com -in1 sim_ft1/test010.ft1    -in2 synth_010.ft1
showDif.com -in1 simNUS_ft1/test010.ft1 -in2 synthNUS_010.ft1 -mask mask_test010.ft1

