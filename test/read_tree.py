#!/usr/bin/env python
"""
NAME
    read_tree.py - a pyframe example script

SYNOPSIS
    ./read_tree.py myntuple.root

DESCRIPTION
    Demonstrates how to read trees in pyframe and make some histograms.

OPTIONS
    -h, --help
        Prints this manual and exits.
        
    -o, --output output.hists.root
        Output file name.

    -t, --tree myntuple
        Input tree name.

AUTHOR
    Ryan Reece  <ryan.reece@cern.ch>

COPYRIGHT
    Copyright 2015 Ryan Reece
    License: GPL <http://www.gnu.org/licenses/gpl.html>

SEE ALSO
    - pyframe <https://github.com/rreece/pyframe/>
    - ROOT <http://root.cern.ch>

TO DO
    - One.
    - Two.

2015-05-26
"""

#------------------------------------------------------------------------------
# imports
#------------------------------------------------------------------------------

## std
import argparse

## ROOT
import ROOT
ROOT.gROOT.SetBatch(True)

## my modules
import pyrootutils
import pyframe


#------------------------------------------------------------------------------
# globals
#------------------------------------------------------------------------------
GeV = 1000.


#------------------------------------------------------------------------------
# options
#------------------------------------------------------------------------------
def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles',  default=None, nargs='+',
            help='Input files as separate args.')
    parser.add_argument('-i', '--input',  default=None,
            help='Input files as a comma-separated list.')   
    parser.add_argument('-o', '--output',  default='output.hists.root',
            help='Name of output file.')   
    parser.add_argument('-t', '--tree',  default='myntuple',
            help='Name of input tree.')   
    ops = parser.parse_args()
    assert ops.infiles
    return ops


#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------
def main():
    ops = options()

    ## get input files and output options
    input_files = list(ops.infiles)
    if ops.input:
        s_input = str(ops.input)
        input_files.extend( s_input.split(',') )
    tree_name = ops.tree
    plot_output = ops.output

    ## make an EventLoop
    loop = pyframe.core.EventLoop('TestLoop', tree=tree_name)
    loop.add_input_files(input_files)

    ## schedule algorithms
    loop += PlotsAlg()

    ## run the event loop
    loop.run()

    print 'Done.'


#------------------------------------------------------------------------------
# PlotsAlg
#------------------------------------------------------------------------------
class PlotsAlg(pyframe.core.Algorithm):
    #__________________________________________________________________________
    def __init__(self, name='PlotsAlg'):
        pyframe.core.Algorithm.__init__(self, name)

    #__________________________________________________________________________
    def execute(self): 
        weight = 1.0

        ## fill event-level histograms
        self.hist('h_w', "ROOT.TH1F('$', ';w;Events', 20, -2.0, 3.0)").Fill(self.chain.w, weight)
        self.hist('h_ph_n', "ROOT.TH1F('$', ';ph_n;Events', 20, -0.5, 19.5)").Fill(self.chain.ph_n, weight)

        ## build VarProxies for photons
        photons = self.chain.build_var_proxies('ph_', self.chain.ph_n)

        ## fill histograms per photon
        for ph in photons:
            self.hist('h_ph_pt', "ROOT.TH1F('$', ';ph_pt;Events / (10 GeV)', 20, 0.0, 200)").Fill(ph.pt/GeV, weight)


#------------------------------------------------------------------------------
if __name__ == '__main__': main()
