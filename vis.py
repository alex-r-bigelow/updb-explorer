#!/usr/bin/env python
import argparse
from resources.pedigree_data import Pedigree

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualizes an ego-pa-ma file; you should have run calculateD.py before running this.')
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
    from resources.main_app import run
    run(ped)
    print "Done."