#!/usr/bin/env python
import argparse, os
from utils.pedigree import Pedigree, gexf_node_attribute_mapper

PORT = 8123

'''## {{{ http://icodesnip.com/snippet/python/simple-stoppable-server-using-socket-timeout
import SimpleHTTPServer, BaseHTTPServer
import socket
import thread
 
class StoppableHTTPServer(BaseHTTPServer.HTTPServer):
 
    def server_bind(self):
        BaseHTTPServer.HTTPServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True
 
    def get_request(self):
        while self.run:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                pass
 
    def stop(self):
        self.run = False
 
    def serve(self):
        while self.run:
            self.handle_request()
 
if __name__=="__main__":
    httpd = StoppableHTTPServer(("127.0.0.1",8080), SimpleHTTPServer.SimpleHTTPRequestHandler)
    thread.start_new_thread(httpd.serve, ())
    raw_input("Press <RETURN> to stop server\n")
    httpd.stop()
## end of http://icodesnip.com/snippet/python/simple-stoppable-server-using-socket-timeout }}}'''

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
    ped = Pedigree(args.infile, countAndCalculate=True, zeroMissing=args.zeroMissing.strip().upper().startswith('T'))
    print "Writing file..."
    extension = os.path.splitext(args.outfile)[1].lower()
    if extension == '.gexf':
        edgeTypes = Pedigree.defaultEdgeTypes()
        nodeAttributeTypes = Pedigree.defaultNodeAttributeTypes()
        
        nodeAttributeTypes['is_root'] = gexf_node_attribute_mapper('is_root', attrType=gexf_node_attribute_mapper.BOOLEAN, defaultValue=False, validValues=[False,True])
        
        # Write the graph file
        ped.write_gexf(args.outfile, edgeTypes, nodeAttributeTypes)
        '''# Copy the graph file locally so it can be served
        shutil.copyfile(args.outfile,'./result.gexf')
        # Grab the freshest versions of the javascript libraries
        shutil.copyfile('../sigma.js/build/sigma.min.js', './sigma.min.js')
        shutil.copyfile('../sigma.js/plugins/sigma.pedigree1.js', './sigma.pedigree1.js')
        shutil.copyfile('../sigma.js/plugins/sigma.parseGexf.js', './sigma.parseGexf.js')
        # Start serving this directory on PORT
        httpd = StoppableHTTPServer(("127.0.0.1",PORT), SimpleHTTPServer.SimpleHTTPRequestHandler)
        thread.start_new_thread(httpd.serve, ())
        # Open the visualization
        webbrowser.open_new_tab('http://127.0.0.1:%i/calculateD.html' % PORT)
        # Let the user shut down the server without having to figure out Ctrl-C
        raw_input("Press <RETURN> to stop web server\n")
        httpd.stop()'''
    elif extension == '.json':
        ped.write_json(args.outfile)
    else:
        ped.write_egopama(args.outfile)
    print "Done."