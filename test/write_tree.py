#!/usr/bin/env python
"""
NAME
    name.py - short description

SYNOPSIS
    Put synposis here.

DESCRIPTION
    Put description here.

OPTIONS
    -h, --help
        Prints this manual and exits.
        
    -n VAL
        Blah blah.

AUTHOR
    Ryan Reece  <ryan.reece@cern.ch>

COPYRIGHT
    Copyright 2010 Ryan Reece
    License: GPL <http://www.gnu.org/licenses/gpl.html>

SEE ALSO
    ROOT <http://root.cern.ch>

TO DO
    - One.
    - Two.

2011-06-15
"""

#------------------------------------------------------------------------------
# imports
#------------------------------------------------------------------------------

## std
import argparse
import time

## ROOT
import ROOT
ROOT.gROOT.SetBatch(True)

## my modules
import pyrootutils


#------------------------------------------------------------------------------
# globals
#------------------------------------------------------------------------------
GeV = 1000.


#------------------------------------------------------------------------------
# options
#------------------------------------------------------------------------------
def options():
    parser = argparse.ArgumentParser()
#    parser.add_argument('infile',  default=None,
#            help='A positional argument.')
#    parser.add_argument('-x', '--option',  default=False,  action='store_true',
#            help="Some toggle option.")
    parser.add_argument('-n', '--nevents',  type=int, default=1000,
            help="Number of events to generate.")
    parser.add_argument('-o', '--output',  default='myntuple.root',
            help="Name of output file.")   
    parser.add_argument('-t', '--tree',  default='myntuple',
            help="Name of input tree.")   
    ops = parser.parse_args()
    assert ops.nevents > 0
    return ops


#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------
def main():
    ops = options()

    timestamp = time.strftime('%Y-%m-%d-%Hh%M')
    print 'Helloworld.  The time is %s.' % timestamp

    ## distributions to draw random test tree from
    f_w = ROOT.TF1('f_w', 'gaus', -2.0, 5.0)
    f_w.SetParameters(1.0, 1.0, 0.2)
    f_ph_n = ROOT.TF1('f_ph_n', 'TMath::Poisson(x, [0])', 0 , 20)
    f_ph_n.SetParameter(0, 3)
    f_ph_pt = ROOT.TF1('f_ph_pt', 'expo', 0.0, 200.0)
    f_ph_pt.SetParameters(0.0, -1.0/100.0)
    f_ph_eta = ROOT.TF1('f_ph_eta', 'pol0', -2.47, 2.47)
    f_ph_eta.SetParameter(0, 1.0)
    f_ph_phi = ROOT.TF1('f_ph_phi', 'pol0', -3.1416, 3.1416)
    f_ph_phi.SetParameter(0, 1.0)

    ## build tree and declare branches
    tw = pyrootutils.TreeWriter(ops.output, ops.tree)

    ## fill tree
    print 'Generating %i events.' % ops.nevents
    for i_event in xrange(ops.nevents):
        progress_interval = 1000
        if i_event % progress_interval == 0 or i_event == ops.nevents-1:
            print '  event %i' % i_event
        event = dict()
        event['w'] =        ( 'F',      f_w.GetRandom()                                                             )
        ph_n = int(f_ph_n.GetRandom())
        event['ph_n'] =     ( 'I',      ph_n                                                                        )
        event['ph_pt'] =    ( 'VF',     [ f_ph_pt.GetRandom()*GeV       for j in xrange(ph_n) ]                     )
        event['ph_eta'] =   ( 'VF',     [ f_ph_eta.GetRandom()          for j in xrange(ph_n) ]                     )
        event['ph_phi'] =   ( 'VF',     [ f_ph_phi.GetRandom()          for j in xrange(ph_n) ]                     )
        event['ph_flags'] = ( 'VVI',    [ [ int(f_ph_phi.GetRandom()) for k in xrange(5) ] for j in xrange(ph_n) ]  )
        tw.fill(event)

    tw.close()
    print 'Done.'


#------------------------------------------------------------------------------
if __name__ == '__main__': main()
