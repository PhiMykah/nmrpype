#!/bin/csh

/bin/rm -rf deco.tab simNUS_ft1 synth_ft1 synthNUS_ft1

touch tmp.tmp
/bin/rm -f tmp*

touch tmp.ft1
/bin/rm -f *.ft1 
