#!/usr/bin/env python
import argparse, webbrowser, shutil, os
from utils.pedigree import Pedigree, gexf_node_attribute_mapper

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualizes an ego-pa-ma file.')
    parser.add_argument('--in', type=str, dest="infile", required = True, help='Path to ego-pa-ma tab-separated file with headers.')
    
    for k,d in Pedigree.REQUIRED_KEYS.iteritems():
        parser.add_argument('--%s'%k, type=str, dest=k, default=d, help='Override the column header for %s. Default is "%s".' % (k,d))
    for k,d in Pedigree.RESERVED_KEYS.iteritems():
        parser.add_argument('--%s'%k, type=str, dest=k, default=d, help='Override the column header for %s. Default is "%s".' % (k,d))
    
    args = parser.parse_args()
    
    for k in Pedigree.REQUIRED_KEYS.keys():
        Pedigree.REQUIRED_KEYS[k] = getattr(args,k)
    for k in Pedigree.RESERVED_KEYS.keys():
        Pedigree.RESERVED_KEYS[k] = getattr(args,k)
    
    print "Loading file..."
    ped = Pedigree(args.infile, countAndCalculate=False)
    print "Starting viz..."
    from Prototypes5.viz import run
    run(ped)
    print "Done."