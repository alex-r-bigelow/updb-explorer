import math
from PySide.QtGui import QColor
from PySide.QtCore import Qt
from pedigree_data import AttributeFilter

class AppComponent(object):
    def notifyChangeHighlightedNode(self, previous, new):
        pass
    def notifyChangeOverlay(self, previous, new):
        pass
    def notifyChangeHighlightedPath(self, previous, new):
        pass
    def notifyTweakVisibleSet(self, previous, new):
        pass
    def notifySetRoot(self, previous, prevSet, new, newSet):
        pass
    def notifyShowSecondRoot(self, previous, prevSet, new, newSet):
        pass
    def notifyChangeScatterplot(self, previousX, previousY, newX, newY):
        pass
    def notifyChangeFilter(self, attr):
        pass
    def notifySetActivePath(self, previous, new):
        pass

class AppState(object):
    '''
    Color schemes obtained from http://geography.uoregon.edu/datagraphics/color_scales.htm
    with slight re-prioritization
    '''
    BACKGROUND_COLOR = Qt.white
    BORDER_COLOR = Qt.white
    ACTIVE_COLOR = QColor.fromRgb(231,41,138)
    ROOT_COLOR = QColor.fromRgb(27,158,119)
    SECOND_ROOT_COLOR = QColor.fromRgb(217,95,2)
    INTERSECTION_COLOR = QColor.fromRgb(117,112,179)
    HIGHLIGHT_COLOR = QColor.fromRgb(230,171,2)
    MISSING_COLOR = Qt.black
    
    CATEGORICAL_COLORS = [QColor.fromHsvF(30.000/360.0,0.500,1.000),  # light orange
                        QColor.fromHsvF(30.000/360.0,1.000,1.000),  # dark orange
                        QColor.fromHsvF(60.000/360.0,0.400,1.000),  # light yellow
                        QColor.fromHsvF(60.000/360.0,0.800,1.000),  # dark yellow
                        QColor.fromHsvF(192.000/360.0,0.350,1.000),  # light blue
                        QColor.fromHsvF(200.000/360.0,0.900,1.000),  # dark blue
                        QColor.fromHsvF(337.500/360.0,0.400,1.000),  # light red
                        QColor.fromHsvF(352.500/360.0,0.889,0.900),  # dark red
                        QColor.fromHsvF(100.000/360.0,0.450,1.000),  # light green
                        QColor.fromHsvF(108.000/360.0,1.000,1.000),  # dark green
                        QColor.fromHsvF(252.000/360.0,0.250,1.000),  # light purple
                        QColor.fromHsvF(248.571/360.0,0.700,1.000)]  # dark purple
    
    ORDINAL_COLORS_3 = [QColor.fromHsvF(0.000/360.0,0.900,0.600),   # Red sequential
                        QColor.fromHsvF(0.000/360.0,0.750,0.700),
                        QColor.fromHsvF(0.000/360.0,0.600,0.800),
                        QColor.fromHsvF(0.000/360.0,0.450,0.900),
                        QColor.fromHsvF(0.000/360.0,0.300,1.000)]
                        
    ORDINAL_COLORS_2 = [QColor.fromHsvF(30.000/360.0,0.900,0.600),   # Orange sequential
                        QColor.fromHsvF(30.000/360.0,0.750,0.700),
                        QColor.fromHsvF(30.000/360.0,0.600,0.800),
                        QColor.fromHsvF(30.000/360.0,0.450,0.900),
                        QColor.fromHsvF(30.000/360.0,0.300,1.000)]
                        
    ORDINAL_COLORS_5 = [QColor.fromHsvF(80.000/360.0,0.900,0.600),   # Green sequential
                        QColor.fromHsvF(80.000/360.0,0.750,0.700),
                        QColor.fromHsvF(80.000/360.0,0.600,0.800),
                        QColor.fromHsvF(80.000/360.0,0.450,0.900),
                        QColor.fromHsvF(80.000/360.0,0.300,1.000)]
                        
    ORDINAL_COLORS_1 = [QColor.fromHsvF(200.000/360.0,0.900,0.600),   # Blue sequential
                        QColor.fromHsvF(200.000/360.0,0.750,0.700),
                        QColor.fromHsvF(200.000/360.0,0.600,0.800),
                        QColor.fromHsvF(200.000/360.0,0.450,0.900),
                        QColor.fromHsvF(200.000/360.0,0.300,1.000)]
                        
    ORDINAL_COLORS_4 = [QColor.fromHsvF(250.000/360.0,0.900,0.600),   # Purple sequential
                        QColor.fromHsvF(250.000/360.0,0.750,0.700),
                        QColor.fromHsvF(250.000/360.0,0.600,0.800),
                        QColor.fromHsvF(250.000/360.0,0.450,0.900),
                        QColor.fromHsvF(250.000/360.0,0.300,1.000)]
    
    @staticmethod
    def blend(color1, color2, percentColor1=0.5):
        pass
    
    def __init__(self, ped):
        self.highlightedNode = None
        self.overlay = None
        self.highlightedPath = []
        self.visibleSet = set()
        self.root = None
        self.rootSet = set()
        self.secondRoot = None
        self.secondRootSet = set()
        self.filters = {}
        self.activePath = []
        self.scatterX = None
        self.scatterY = None
        
        self.binColors = True
        
        self.ped = ped
        self.headers = [self.ped.REQUIRED_KEYS['personID']]
        self.headers.extend(self.ped.extraNodeAttributes)
        for h in self.headers:
            self.filters[h] = AttributeFilter(self.ped.attrDetails[h], self)
        
        self.components = set()
    
    def registerComponent(self, c):
        self.components.add(c)
        
    def adjustOrdinalValue(self, value):
        # TODO: the histogram will be able to change the color map... we need to map values to colors accordingly
        return value
    
    def getOrdinalColor(self, value, alternate=1):
        if self.binColors:
            lowerIndex = int(math.floor(4.0*value))
            higherIndex = int(math.ceil(4.0*value))
            closerIndex = lowerIndex if value-math.floor(value) < math.ceil(value)-value else higherIndex
            if alternate == 2:
                return AppState.ORDINAL_COLORS_2[closerIndex]
            elif alternate == 3:
                return AppState.ORDINAL_COLORS_3[closerIndex]
            elif alternate == 4:
                return AppState.ORDINAL_COLORS_4[closerIndex]
            elif alternate == 5:
                return AppState.ORDINAL_COLORS_5[closerIndex]
            else:
                return AppState.ORDINAL_COLORS_1[closerIndex]
        else:
            if alternate == 2:
                hue = AppState.ORDINAL_COLORS_2[0]
            elif alternate == 3:
                hue = AppState.ORDINAL_COLORS_3[0]
            elif alternate == 4:
                hue = AppState.ORDINAL_COLORS_4[0]
            elif alternate == 5:
                hue = AppState.ORDINAL_COLORS_5[0]
            else:
                hue = AppState.ORDINAL_COLORS_1[0]
            return QColor.fromHsvF(hue.hueF(),0.9-0.6*value,0.6+0.4*value)
    
    def getColorForValue(self, v, attr, alternate=1):
        if v == None or not self.ped.attrDetails.has_key(attr):
            return AppState.MISSING_COLOR
        else:
            v = self.ped.attrDetails[attr].getProportionOrClass(v)
            if isinstance(v,float):
                return self.getOrdinalColor(self.adjustOrdinalValue(v), alternate)
            else:
                return AppState.CATEGORICAL_COLORS[v]
    
    def getColors(self, personID, alternate=1):
        showFan = False
        if self.overlay == None:
            fill = AppState.MISSING_COLOR
        else:
            fill = self.getColorForValue(self.ped.getAttribute(personID,self.overlay,None), self.overlay, alternate)
        if personID == self.highlightedNode:
            stroke = AppState.HIGHLIGHT_COLOR
            showFan = True
        elif personID == self.secondRoot:
            stroke = AppState.SECOND_ROOT_COLOR
        elif personID == self.root:
            stroke = AppState.ROOT_COLOR
        else:
            stroke = AppState.BORDER_COLOR
        return (fill,stroke,showFan)
    
    def getDirectionColor(self, peopleIDs, alternate=1):
        # TODO
        pass
    
    def getPathColor(self, source, target):
        for s,t in self.highlightedPath:
            if (s == source and t == target) or (s == target and t == source):
                return AppState.HIGHLIGHT_COLOR
        for s,t in self.activePath:
            if (s == source and t == target) or (s == target and t == source):
                return AppState.ACTIVE_COLOR
        return AppState.MISSING_COLOR
    
    def changeHighlightedNode(self, n):
        previous = self.highlightedNode
        self.highlightedNode = n
        for c in self.components:
            c.notifyChangeHighlightedNode(previous, n)
    def changeOverlay(self, attr):
        previous = self.overlay
        self.overlay = attr
        for c in self.components:
            c.notifyChangeOverlay(previous, attr)
    def changeHighlightedPath(self, p):
        previous = self.highlightedPath
        self.highlightedPath = p
        for c in self.components:
            c.notifyChangeHighlightedPath(previous, p)
    def tweakVisibleSet(self, s):
        previous = self.visibleSet
        self.visibleSet = s
        for c in self.components:
            c.notifyTweakVisibleSet(previous, s)
    def setRoot(self, r):
        previous = self.root
        prevSet = self.rootSet
        self.root = r
        self.secondRoot = None
        self.secondRootSet = set()
        if r != None:
            self.rootSet = set(self.ped.iterDown(r))
        else:
            self.rootSet = set()
        self.tweakVisibleSet(self.rootSet)
        for c in self.components:
            c.notifySetRoot(previous, prevSet, self.root, self.rootSet)
    def showSecondRoot(self, r):
        if self.root == None:
            self.setRoot(r)
            return
        elif self.root == r:
            r = None
        
        if self.secondRoot == r:
            self.setRoot(r)
            previous = self.secondRoot
            prevSet = self.secondRootSet
            self.secondRoot = None
            self.secondRootSet = set()
        else:
            previous = self.secondRoot
            prevSet = self.secondRootSet
            if len(prevSet) > 0:
                self.tweakVisibleSet(self.visibleSet.difference(prevSet))
            self.secondRoot = r
            if r != None:
                self.secondRootSet = set(self.ped.iterDown(r)).difference(self.visibleSet)
            else:
                self.secondRootSet = set()
            self.tweakVisibleSet(self.secondRootSet.union(self.visibleSet))
        for c in self.components:
            c.notifyShowSecondRoot(previous, prevSet, self.secondRoot, self.secondRootSet)
    def changeScatterplot(self, scatterX, scatterY):
        lastX = scatterX
        lastY = scatterY
        self.scatterX = scatterX
        self.scatterY = scatterY
        for c in self.components:
            c.notifyChangeScatterplot(lastX,lastY,self.scatterX,self.scatterY)
    def notifySetActivePath(self, previous, p):
        previous = self.activePath
        self.activePath = p
        for c in self.components:
            c.notifySetActivePath(previous, p)