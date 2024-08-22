#!/bin/csh

/bin/rm -rf mask.ft1 sim.ft1 simNUS.ft1 synth_ft1 synthNUS_ft1

mkdir synth_ft1 synthNUS_ft1

addNMR -in1 sim_ft1/test%03d.ft1 -in2 mask_ft1/test%03d.ft1 -out simNUS_ft1/test%03d.ft1 -mult

xyz2pipe -in sim_ft1/test%03d.ft1     -out simNUS.ft1
xyz2pipe -in simNUS_ft1/test%03d.ft1  -out sim.ft1
xyz2pipe -in mask_ft1/test%03d.ft1    -out mask.ft1

cd sim_ft1
   set fList = (*.ft1)
cd ../

foreach f ($fList)
   echo sim_ft1/$f

   deco2D.tcl -in sim_ft1/$f    -mask None -basis basis_ft1/*.ft1 -out synth_ft1/$f
   deco2D.tcl -in simNUS_ft1/$f -mask mask_ft1/$f -basis basis_ft1/*.ft1 -out synthNUS_ft1/$f

   echo ""
   showDif.com -in1 sim_ft1/$f -in2 synth_ft1/$f    -mask None
   showDif.com -in1 sim_ft1/$f -in2 synthNUS_ft1/$f -mask mask_ft1/$f
   echo ""
end

xyz2pipe -in synth_ft1/test%03d.ft1     -out synth.ft1
xyz2pipe -in synthNUS_ft1/test%03d.ft1  -out synthNUS.ft1

