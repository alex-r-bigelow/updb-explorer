import networkx, sys, math

class Pedigree:
    CHILD_TO_PARENT = 1
    PARENT_TO_CHILD = 2
    HUSBAND_TO_WIFE = 3
    WIFE_TO_HUSBAND = 4
    
    EDGE_TYPES = {CHILD_TO_PARENT:'CHILD_TO_PARENT',
                  PARENT_TO_CHILD:'PARENT_TO_CHILD',
                  HUSBAND_TO_WIFE:'HUSBAND_TO_WIFE',
                  WIFE_TO_HUSBAND:'WIFE_TO_HUSBAND'}
    
    REQUIRED_KEYS = {'personID':'personID',
                     'paID':'paID',
                     'maID':'maID',
                     'sex':'sex',
                     'affected':'affected'}
    RESERVED_KEYS = {'n_local_aff':'n_local_aff',
                     'n_local_desc':'n_local_desc',
                     'nicki_d':'nicki_d',
                     'is_root':'is_root',
                     'is_leaf':'is_leaf',
                     'generation':'generation'}
    
    INV_LOG_TWO = 1.0/math.log(2.0)
    
    KEY_ERROR = KeyError('dummy')
    
    def __init__(self, path, countAndCalculate=True):
        self.g = networkx.DiGraph()
        self.rowOrder = []
        self.extraNodeAttributes = []
        
        # TODO: parse other file formats based on their extension
        self._parseEgoPaMa(path, countAndCalculate)
        
        if countAndCalculate:
            self._countAndCalculate()
    
    def _parseEgoPaMa(self, path, countAndCalculate):
        required_indices = {}
        reserved_indices = {}
        
        with open(path,'rb') as infile:
            header = None
            for line in infile:
                columns = line.strip().split('\t')
                if header == None:
                    header = columns
                    for k,v in Pedigree.REQUIRED_KEYS.iteritems():
                        if v not in header:
                            raise Exception('Required header "%s" not in file.' % v)
                        required_indices[k] = header.index(v)
                    for k,v in Pedigree.RESERVED_KEYS.iteritems():
                        if v in header:
                            if countAndCalculate:
                                sys.stderr.write('WARNING: "%s" is a reserved header - this column may be overwritten.\n' % v)
                            reserved_indices[k] = header.index(v)
                        else:
                            reserved_indices[k] = len(header)
                            header.append(v)
                    self.extraNodeAttributes = list(header)
                    self.extraNodeAttributes.pop(required_indices['personID'])
                    continue
                else:
                    personID = columns[required_indices['personID']]
                    try:
                        int(personID)
                    except ValueError:
                        raise Exception('Non-numeric personID: %s' % personID)
                    self.rowOrder.append(personID)
                    
                    attribs = list(columns)
                    
                    # try to interpret data types
                    for i,a in enumerate(attribs):
                        if i == required_indices['personID'] or i == required_indices['paID'] or i == required_indices['maID']:
                            continue
                        elif i == required_indices['sex']:
                            a = a.strip()
                            if len(a) < 1:
                                attribs[i] = '?'
                            else:
                                attribs[i] = a.upper()[0]
                        elif i == required_indices['affected'] or i == reserved_indices.get('is_root',None) or i == reserved_indices.get('is_leaf',None):
                            if a != '0' and a != '1':
                                attribs[i] = None
                            else:
                                attribs[i] = True if a == '1' else False
                        elif a == '':
                                attribs[i] = None
                        else:
                            try:
                                attribs[i] = float(a)
                            except ValueError:
                                pass
                    
                    attribs.pop(required_indices['personID'])
                    
                    self.g.add_node(personID,dict(zip(self.extraNodeAttributes,attribs)))
                    
                    paID = self.getAttribute(personID, 'paID', '0')
                    maID = self.getAttribute(personID, 'maID', '0')
                    if paID != '0':
                        self.g.add_edge(personID,paID,{'type':Pedigree.CHILD_TO_PARENT})
                        self.g.add_edge(paID,personID,{'type':Pedigree.PARENT_TO_CHILD})
                        self.setAttribute(paID, 'sex', 'M')
                    if maID != '0':
                        self.g.add_edge(personID,maID,{'type':Pedigree.CHILD_TO_PARENT})
                        self.g.add_edge(maID,personID,{'type':Pedigree.PARENT_TO_CHILD})
                        self.setAttribute(maID, 'sex', 'F')
                    # If I write my own dijkstra's for self.countAndCalculate, I could always just add the marriage links here
                    if not countAndCalculate and paID != '0' and maID != '0':
                        self.g.add_edge(paID,maID,{'type':Pedigree.HUSBAND_TO_WIFE})
                        self.g.add_edge(maID,paID,{'type':Pedigree.WIFE_TO_HUSBAND})
        infile.close()
        # Need to also add ancestors that are mentioned but not explicitly detailed in the file
        temp = set(self.rowOrder)
        for p in self.g.node.iterkeys():
            if p not in temp:
                self.rowOrder.append(p)
                temp.add(p)
    
    def _countAndCalculate(self):
        # If I write my own dijkstra's, I can just toss this and use the real one
        def stupidIterSpouses(person):
            visited = set()
            for child in self.iterChildren(person):
                for spouse in self.iterParents(child):
                    if spouse in visited:
                        continue
                    visited.add(spouse)
                    yield spouse
        
        # Flag roots and leaves, count descendants, collect affecteds, get starting point for generation counting
        generationStart = self.rowOrder[0]
        generationCount = 0
        for p in self.rowOrder:
            self.setAttribute(p, 'is_root', self.isRoot(p))
            self.setAttribute(p, 'is_leaf', self.isLeaf(p))
            
            self.setAttribute(p, 'n_local_desc', 0)
            self.setAttribute(p, 'n_local_aff', set())
            for d in self.iterDown(p):
                self.setAttribute(p, 'n_local_desc', self.getAttribute(p, 'n_local_desc') + 1)
                if self.getAttribute(d, 'affected', None) == True:
                    self.getAttribute(p, 'n_local_aff').add(d)
            if self.getAttribute(p, 'n_local_desc') > generationCount:
                generationCount = self.getAttribute(p, 'n_local_desc')
                generationStart = p
            # We need a consistent ordering of affecteds to calculate d
            self.setAttribute(p, 'n_local_aff', sorted(self.getAttribute(p, 'n_local_aff')))
        
        # Calculate generations
        generationVisitCount = len(self.rowOrder)
        while True:
            # Store the generation number, and keep track of how far up we go relative to us
            error = 0
            for p,g in self.iterGenerations(generationStart):
                error = min(error,g)
                self.setAttribute(p, 'generation', g)
                generationVisitCount -= 1
            
            # Okay, now adjust for the error we saw
            if error < 0:
                for p,g in self.iterGenerations(generationStart):
                    self.setAttribute(p, 'generation', self.getAttribute(p, 'generation') - error)
            
            # Finally, if there are any unconnected components to the section we just did, we need to
            # keep working there... grab the first non-counted person we see
            if generationVisitCount > 0:
                for p in self.rowOrder:
                    if self.getAttribute(p, 'generation', None) == None:
                        generationStart = p
                        # TODO: I probably ought to fly as high up as possible for better results
                        break
            else:
                break
        
        # Calculate d
        for p in self.rowOrder:
            p_aff = self.getAttribute(p, 'n_local_aff')
            if len(p_aff) <= 1:
                self.setAttribute(p, 'nicki_d', None)
            else:
                d = 0.0
                for i,a in enumerate(p_aff):
                    for b in p_aff[i+1:]:
                        meioses = networkx.dijkstra_path_length(self.g, a, b, 1.0)
                        commonAncestors = 1.0
                        for s in stupidIterSpouses(p):
                            s_aff = self.getAttribute(s, 'n_local_aff')
                            if a in s_aff and b in s_aff:
                                commonAncestors += 1.0
                        d += -math.log(commonAncestors*0.5**(meioses+1))*Pedigree.INV_LOG_TWO
                self.setAttribute(p, 'nicki_d', d/(len(p_aff)-1))
        # Okay, we don't need the lists anymore... just keep the counts
        for p in self.rowOrder:
            self.setAttribute(p, 'n_local_aff', len(self.getAttribute(p, 'n_local_aff')))
        
        # Now add spouse links - if I write my own dijkstra's for this method, I can toss this last section too
        for p in self.rowOrder:
            paID = self.dad(p)
            maID = self.mom(p)
            if paID != None and maID != None:
                self.g.add_edge(paID,maID,{'type':Pedigree.HUSBAND_TO_WIFE})
                self.g.add_edge(maID,paID,{'type':Pedigree.WIFE_TO_HUSBAND})
    
    def dad(self, person):
        for parent in self.iterParents(person):
            if self.getAttribute(parent, 'sex') == 'M':
                return parent
        return None
    
    def mom(self, person):
        for parent in self.iterParents(person):
            if self.getAttribute(parent, 'sex') == 'F':
                return parent
        return None
    
    def iterParents(self, person):
        for parent,attrs in self.g.edge[person].iteritems():
            if not attrs['type'] == Pedigree.CHILD_TO_PARENT:
                continue
            yield parent
    
    def iterChildren(self, person):
        for child,attrs in self.g.edge[person].iteritems():
            if not attrs['type'] == Pedigree.PARENT_TO_CHILD:
                continue
            yield child
        
    def iterSpouses(self, person):
        for spouse,attrs in self.g.edge[person].iteritems():
            if not attrs['type'] == Pedigree.HUSBAND_TO_WIFE or attrs['type'] == Pedigree.WIFE_TO_HUSBAND:
                continue
            yield spouse
    
    def iterNuclear(self, person):
        # return the person and the relationship in a tuple in a nuclear family
        for p,attrs in self.g.edge[person].iteritems():
            yield (p,attrs['type'])
    
    def iterUp(self,person):
        # BFS using a queue
        toVisit = [person]
        visited = set()
        while len(toVisit) > 0:
            p = toVisit.pop(0)
            if not p in visited:
                visited.add(p)
                toVisit.extend(self.iterParents(p))
                yield p
    
    def iterDown(self,person):
        # BFS using a queue
        toVisit = [person]
        visited = set()
        while len(toVisit) > 0:
            p = toVisit.pop(0)
            if not p in visited:
                visited.add(p)
                toVisit.extend(self.iterChildren(p))
                yield p
    
    def iterDownWithSpouses(self, person):
        # BFS using a queue
        toVisit = [person]
        visited = set()
        spouses = set()
        while len(toVisit) > 0:
            p = toVisit.pop(0)
            if not p in visited:
                visited.add(p)
                toVisit.extend(self.iterChildren(p))
                spouses.update(self.iterSpouses(p))
                yield p
        for s in spouses:
            if s not in visited:
                yield s
    
    def iterGenerations(self,person):
        # Iterates down then up BFS style, yielding tuples with the person and the generation number relative to the starting point
        toVisit = [(person,0)]
        visited = {}
        error = 0
        while len(toVisit) > 0:
            p,g = toVisit.pop(0)
            if not visited.has_key(p):
                visited[p] = g
                for c in self.iterChildren(p):
                    toVisit.append((c,g+1))
                for c in self.iterParents(p):
                    toVisit.append((c,g-1))
                yield (p,g)
    
    def isRoot(self, person):
        for parent in self.iterParents(person):
            return False
        return True
    
    def isLeaf(self,person):
        for child in self.iterChildren(person):
            return False
        return True
    
    def getAttribute(self, p, a, default=KEY_ERROR):
        a = Pedigree.REQUIRED_KEYS.get(a,a)
        a = Pedigree.RESERVED_KEYS.get(a,a)
        if not self.g.node[p].has_key(a) and isinstance(default,KeyError):
            raise KeyError(a)
        else:
            return self.g.node[p].get(a,default)
    
    def setAttribute(self, p, a, v):
        a = Pedigree.REQUIRED_KEYS.get(a,a)
        a = Pedigree.RESERVED_KEYS.get(a,a)
        self.g.node[p][a] = v
    
    def getStringAttribute(self, p, a):
        value = self.getAttribute(p, a, None)
        if value == None:
            value = ''
        elif isinstance(value,bool):
            value = '1' if value else '0'
        else:
            value = str(value)
        return value
    
    def getJSONAttribute(self, p, a):
        value = self.getAttribute(p, a, None)
        if value == None:
            value = 'null'
        elif isinstance(value,bool):
            value = 'true' if value else 'false'
        elif isinstance(value,float):
            value = '%f' % value
        elif isinstance(value,int):
            value = '%i' % value
        elif not isinstance(value,str):
            value = str(value)
        else:
            value = '"%s"' % value
        return value
        
    @staticmethod
    def defaultEdgeTypes():
        '''
        Some default edge mappings...
        '''
        edgeTypes = {}
        
        edgeTypes[Pedigree.PARENT_TO_CHILD] = gexf_edge_type_mapper(edgeType=gexf_edge_type_mapper.DIRECTED,
                                                                    edgeShape=gexf_edge_type_mapper.SOLID,
                                                                    edgeWeight=1.0,
                                                                    edgeThickness=1.0,
                                                                    edgeColor=(255,255,255,1.0))
        edgeTypes[Pedigree.HUSBAND_TO_WIFE] = gexf_edge_type_mapper(edgeType=gexf_edge_type_mapper.UNDIRECTED,
                                                                    edgeShape=gexf_edge_type_mapper.SOLID,
                                                                    edgeWeight=0.5,
                                                                    edgeThickness=1.0,
                                                                    edgeColor=(255,255,255,0.5))
        return edgeTypes
    @staticmethod
    def defaultNodeAttributeTypes():
        '''
        Some default node attribute mappings...
        '''
        nodeAttributeTypes = {}
        
        def mapSexToShape(value):
            if value == 'M':
                return 'square'
            elif value == 'F':
                return 'disc'
            else:
                return 'diamond'
        
        sexKey = Pedigree.REQUIRED_KEYS['sex']
        nodeAttributeTypes[sexKey] = gexf_node_attribute_mapper(sexKey,gexf_node_attribute_mapper.STRING,'?',['M','F','?'])
        nodeAttributeTypes[sexKey].mapToViz(gexf_node_attribute_mapper.SHAPE,mapSexToShape)
        
        def mapAffectedToColor(value):
            if value == True:
                return (255,0,0,1.0)
            elif value == False:
                return (255,255,255,1.0)
            else:
                return (255,255,255,0.5)
        
        affectedKey = Pedigree.REQUIRED_KEYS['affected']
        nodeAttributeTypes[affectedKey] = gexf_node_attribute_mapper(affectedKey,gexf_node_attribute_mapper.BOOLEAN,False,[True,False,None])
        nodeAttributeTypes[affectedKey].mapToViz(gexf_node_attribute_mapper.COLOR,mapAffectedToColor)
        
        return nodeAttributeTypes
    
    def write_gexf(self, path, edgeTypes=None, nodeAttributeTypes=None):
        '''
        gexf supports richer edges than networkx: all edges WILL BE EXCLUDED unless the edge type is specified via the edgeTypes parameter
        
        gexf has two places for node attributes: as tag attributes or as child tags. Unless specified via the nodeAttributeTypes parameter,
        all attributes will be assumed to be tag attributes. Child tags have more semantics - they need to know the data type and in some cases all possible values.
        '''
        
        if edgeTypes == None:
            edgeTypes = Pedigree.defaultEdgeTypes()
        if nodeAttributeTypes == None:
            nodeAttributeTypes = Pedigree.defaultNodeAttributeTypes()
        
        with open(path,'wb') as outfile:
            # header crap
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            outfile.write('<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:viz="http://www.gexf.net/1.2draft/viz">\n')
            outfile.write('<graph>\n')
            # node attribute definitions
            outfile.write('<attributes class="node" mode="static">\n')
            attributeIDs = []
            for k,naType in nodeAttributeTypes.iteritems():
                definition = naType.formatDefinition()
                if definition == None:
                    continue
                else:
                    outfile.write(definition+'\n')
                    attributeIDs.append(k)
            outfile.write('</attributes>\n')
            # nodes
            outfile.write('<nodes>\n')
            for p in self.rowOrder:
                outfile.write('<node id="%s" label="%s"' % (p,p))
                subnodes = []
                for a in self.extraNodeAttributes:
                    if not nodeAttributeTypes.has_key(a):
                        outfile.write(' %s="%s"' % (a,self.getStringAttribute(p, a)))
                    else:
                        if not a in attributeIDs:
                            index = -1
                        else:
                            index = attributeIDs.index(a)
                        subnodes.append(nodeAttributeTypes[a].formatAttValue(index,self.g.node[p].get(a,None)))
                if len(subnodes) > 0:
                    outfile.write('>\n')
                    outfile.write('<attvalues>\n')
                    outfile.write('\n'.join(subnodes))
                    outfile.write('\n</attvalues>\n')
                    outfile.write('</node>\n')
                else:
                    outfile.write('/>\n')
            outfile.write('</nodes>')
            
            # edges
            outfile.write('<edges>\n')
            for source,edges in self.g.edge.iteritems():
                for target,attrs in edges.iteritems():
                    eMap = edgeTypes.get(attrs['type'],None)
                    if eMap == None:
                        continue
                    else:
                        outfile.write(eMap.formatEdge(source,target) + '\n')
            outfile.write('</edges>\n')
            
            # footer crap
            outfile.write('</graph>\n')
            outfile.write('</gexf>')
        outfile.close()
    
    def write_egopama(self, path):
        with open(path,'wb') as outfile:
            outfile.write(Pedigree.REQUIRED_KEYS['personID'])
            outfile.write('\t')
            outfile.write('\t'.join(self.extraNodeAttributes))
            outfile.write('\n')
            for p in self.rowOrder:
                outfile.write(p)
                
                dad = self.dad(p)
                if dad == None:
                    dad = '0'
                outfile.write('\t%s' % dad)
                
                mom = self.mom(p)
                if mom == None:
                    mom = '0'
                outfile.write('\t%s' % mom)
                for a in self.extraNodeAttributes[2:]:
                    outfile.write('\t%s' % self.getStringAttribute(p, a))
                outfile.write('\n')
        outfile.close()
    
    def write_json(self, path):
        with open(path,'wb') as outfile:
            outfile.write('{\n')
            # Write individuals
            outfile.write('"individuals": [\n')
            individualList = ""
            for i,p in enumerate(self.rowOrder):
                individualList += '\t{"%s":"%s"' % (Pedigree.REQUIRED_KEYS['personID'],p)
                for a in self.extraNodeAttributes:
                    individualList += ',"%s":%s' % (a,self.getJSONAttribute(p, a))
                individualList += '},\n'
            outfile.write('%s]\n' % individualList[:-2])  # switch the ,\n for ]\n
            # Write each type of link
            for t,s in Pedigree.EDGE_TYPES.iteritems():
                outfile.write(',"%s": [\n' % s)
                edgeList = ""
                for i,source in enumerate(self.rowOrder):
                    for target, attrs in self.g.edge[source].iteritems():
                        if attrs['type'] == t:
                            j = self.rowOrder.index(target)
                            edgeList += '\t{"source":"%i","target":"%i"},\n' % (i,j)    # this indexing is a little dumb, but oh, well (vega does it this way...)
                outfile.write('%s]\n' % edgeList[:-2])
            outfile.write('}')
        outfile.close()


'''
General gexf notes:
    Overall structure is 
    
    <gexf>
        <meta>
        <graph>                                has a defaultedgetype=any of 'directed','undirected','mutual'
            <attributes>
            <nodes>
            <edges>
    
    
    Should start with <gexf xmlns="http://www.gexf.net/1.2draft/viz">
    To use any of the viz options, we need to add xmlns:viz="http://www.gexf.net/1.2draft/viz" as well
    
    Custom node attributes should be declared like this:
    <attributes class="node" mode="static">                        always use "static" ... other option is "dynamic", and is used for time-changing graphs
        <attribute id="0" title="url" type="string"/>
        <attribute id="1" title="frog" type="boolean">            type can be 'integer','long','double','float','boolean','liststring','string','anyURI'
            <default>true</default>
        </attribute>
    </attributes>
    and used like this:
    <node id="0" label="myNode">
        <attvalues>
            <attvalue for="0" value="http://www.example.com"/>
            <attvalue for="1" value="false"/>
        </attvalues>
    </node>
    
    I assume edges work the same way?
'''
class gexf_edge_type_mapper:
    # type
    DIRECTED = 'directed'
    UNDIRECTED = 'undirected'
    MUTUAL = 'mutual'
    
    # viz:shape
    SOLID = 'solid'
    DOTTED = 'dotted'
    DASHED = 'dashed'
    DOUBLE = 'double'
    
    LAST_ID = 0
    
    '''
    gexf tag attributes:
        id*        int
        source*    int
        target*    int
        weight    float, default 1.0
        label    string
        type    one of 'directed','undirected','mutual'
        start,end    date/time?
        
    gexf internal attributes:
        viz:size         value=float                      usually between 1 - 10? Does this override weight?
        viz:shape        value=one of 'solid','dotted','dashed','double'
        viz:color        r=0 to 255, g=0 to 255, b=0 to 255, a=0.0 to 1.0
    '''
    def __init__(self, edgeType=UNDIRECTED,
                       edgeShape=SOLID,
                       edgeWeight=1.0,
                       edgeThickness=1.0,
                       edgeColor=(0,0,0,1.0)):
        self.edgeType = edgeType
        self.edgeShape = edgeShape
        self.edgeWeight = edgeWeight
        self.edgeThickness = edgeThickness
        self.edgeColor = edgeColor
    
    def formatEdge(self, source, target):
        result = '<edge id="%i" source="%s" target="%s" type="%s" weight="%f">\n' % (gexf_edge_type_mapper.LAST_ID,source,target,self.edgeType,self.edgeWeight)
        gexf_edge_type_mapper.LAST_ID += 1
        result += '<viz:shape value="%s"/>\n' % self.edgeShape
        result += '<viz:thickness value="%f"/>\n' % self.edgeThickness
        result += '<viz:color r="%i" g="%i" b="%i" a="%f"/>\n' % self.edgeColor
        result += '</edge>'
        return result

class gexf_node_attribute_mapper:
    INTEGER='integer'
    LONG='long'
    DOUBLE='double'
    FLOAT='float'
    BOOLEAN='boolean'
    LISTSTRING='liststring'
    STRING='string'
    ANYURI='anyURI'
    
    LAST_ID = 0
    
    COLOR = 'viz:color'
    POSITION = 'viz:position'
    SIZE = 'viz:size'
    SHAPE = 'viz:shape'
    VIZ_TAGS = set([COLOR,POSITION,SIZE,SHAPE])
    
    '''
    gexf tag attributes:
        id*       int
        label    string
        start,end     date/time?
        
    gexf internal attributes:
        viz:color        r=0 to 255, g=0 to 255, b=0 to 255, a=0.0 to 1.0
        viz:position     x=float, y=float, z=float        z is usually 0.0, and x and y should probably be between 0 - 100?
        viz:size         value=float                      usually between 1 - 10?
        viz:shape        value=one of 'disc','square','triangle','diamond','image'        if 'image', also needs uri=url (or path?)
    '''
    def __init__(self, title, attrType=STRING, defaultValue=None, validValues=None):
        self.myID = gexf_node_attribute_mapper.LAST_ID
        gexf_node_attribute_mapper.LAST_ID += 1
        self.title = title
        self.attrType = attrType
        self.defaultValue = defaultValue
        self.validValues = validValues
        self.mapToVizTag = None
        self.mapToVizValue = None
    
    def mapToViz(self, tag, function):
        assert tag in gexf_node_attribute_mapper.VIZ_TAGS
        self.mapToVizTag = tag
        self.mapToVizValue = function
    
    def formatDefinition(self):
        if self.mapToVizTag != None:
            return None
        result = '<attribute id="%i" title="%s" type="%s"' % (self.myID,self.title,self.attrType)
        if self.defaultValue != None or self.validValues != None:
            result += '>\n'
        else:
            result += '/>'
            return result
        
        if self.defaultValue != None:
            result += '<default>%s</default>\n' % str(self.defaultValue)
        if self.validValues != None:
            result += '<options>%s</options>\n' % '|'.join(str(v) for v in self.validValues)
        result += '</attribute>'
        return result
    
    def formatAttValue(self, index, value):
        if self.mapToVizTag != None:
            if self.mapToVizTag == gexf_node_attribute_mapper.COLOR:
                return '<viz:color r="%i" g="%i" b="%i" a="%f"/>' % self.mapToVizValue(value)
            elif self.mapToVizTag == gexf_node_attribute_mapper.POSITION:
                return '<viz:position x="%f" y="%f" z="%f"/>' % self.mapToVizValue(value)
            elif self.mapToVizTag == gexf_node_attribute_mapper.SIZE:
                return '<viz:size value="%f"/>' % self.mapToVizValue(value)
            elif self.mapToVizTag == gexf_node_attribute_mapper.SHAPE:
                return '<viz:shape value="%s"/>' % self.mapToVizValue(value)
        else:
            return '<attvalue for="%i" value="%s"/>' % (index,value)