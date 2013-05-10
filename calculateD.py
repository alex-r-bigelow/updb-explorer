#!/usr/bin/env python
import argparse, os
from resources.pedigree_data import Pedigree, gexf_node_attribute_mapper

def tick(newMessage=None,increment=1):
    if newMessage != None:
        print newMessage

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculates Nicki\'s d statistic given an ego-pa-ma file.')
    parser.add_argument('--in', type=str, dest="infile", required = True, help='Path to ego-pa-ma tab-separated file with headers.')
    parser.add_argument('--out', type=str, dest="outfile", required = True, help='Path to write the same ego-pa-ma with additional columns.')
    parser.add_argument('--zeroMissingLines', type=str, dest="zeroMissing", required=False, nargs="?", default="False", const="True",
                        help="If True, this will only calculate values for lines in the file (and replace missing parents with zeros). " + 
                        "Otherwise, lines will be added for any individual mentioned in the file.")
    
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
    ped = Pedigree(args.infile, countAndCalculate=True, zeroMissing=args.zeroMissing.strip().upper().startswith('T'), tickFunction=tick, numTicks = 100)
    print "Writing file..."
    lowPath = args.outfile.lower()
    if lowPath.endswith('.gexf'):
        edgeTypes = Pedigree.defaultEdgeTypes()
        nodeAttributeTypes = Pedigree.defaultNodeAttributeTypes()
        nodeAttributeTypes['is_root'] = gexf_node_attribute_mapper('is_root', attrType=gexf_node_attribute_mapper.BOOLEAN, defaultValue=False, validValues=[False,True])
        
        # Write the graph file
        ped.write_gexf(args.outfile, edgeTypes, nodeAttributeTypes)
    elif lowPath.endswith('.json'):
        ped.write_json(args.outfile)
    elif lowPath.endswith('.dot'):
        ped.write_dot(args.outfile)
    elif lowPath.endswith('.png'):
        program = lowPath[:-4].split('.')[-1]
        ped.write_image(args.outfile, program)
    else:
        ped.write_egopama(args.outfile)
    print "Done."