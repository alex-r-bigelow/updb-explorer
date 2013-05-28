import math, networkx
from colormath.color_objects import LabColor, RGBColor
from PySide.QtGui import QColor, QMenu, QCursor
from PySide.QtCore import Qt
from pedigree_data import AttributeFilter

class AppComponent(object):
    def notifyHighlightAnIndividual(self, previous, new):
        pass
    def notifyShowIndividualDetails(self, new):
        pass
    def notifyChangePedigreeA(self, previousID, newID):
        pass
    def notifyChangePedigreeB(self, previousID, newID):
        pass
    def notifyHighlightHistory(self, previous, new):
        pass
    def notifyChangeOverlay(self, previous, new):
        pass
    def notifyChangeFilters(self, previous, new):
        pass
    def notifyShowScatterplot(self, previous, new):
        pass
    def notifyChangePathTargets(self, previous, new):
        pass
    def notifyHighlightPath(self, previous, new):
        pass
    def notifyChangePreferences(self, previous, new):
        pass

class AppPreferences(object):
    def __init__(self):
        self.binColors = True

class AppState(object):
    '''
    Color scheme obtained from colorbrewer2.org
    '''
    BACKGROUND_COLOR = Qt.black
    BORDER_COLOR = Qt.black
    A_COLOR = QColor.fromRgb(51,160,44)   # dark green
    B_COLOR = QColor.fromRgb(178,223,138)   # light green
    INTERSECTION_COLOR = QColor.fromRgb(110,193,90)   # blend of the two
    HIGHLIGHT_COLOR = QColor.fromRgb(255,255,153)   # yellow
    MISSING_COLOR = Qt.white
    
    CATEGORICAL_COLORS = [QColor.fromRgb(166, 206, 227),    # blues
                          QColor.fromRgb(31, 120, 180),
                          QColor.fromRgb(253, 191, 111),    # oranges
                          QColor.fromRgb(255, 127, 0),
                          QColor.fromRgb(202, 178, 214),    # purples
                          QColor.fromRgb(106, 61, 154),
                          QColor.fromRgb(251, 154, 153),    # reds
                          QColor.fromRgb(227, 26, 28),
                          QColor.fromRgb(178, 223, 138),    # greens - already using for set stuff
                          QColor.fromRgb(51, 160, 44),
                          QColor.fromRgb(255, 255, 153)]    # yellow - already using for highlight
    
    ORDINAL_COLORS_1 = [QColor.fromRgb(166, 206, 227),    # blues
                        QColor.fromRgb(31, 120, 180)]
    
    ORDINAL_COLORS_2 = [QColor.fromRgb(253, 191, 111),    # oranges
                        QColor.fromRgb(255, 127, 0)]
    
    ORDINAL_COLORS_3 = [QColor.fromRgb(202, 178, 214),    # purples
                        QColor.fromRgb(106, 61, 154)]
    
    ORDINAL_COLORS_4 = [QColor.fromRgb(251, 154, 153),    # reds
                        QColor.fromRgb(227, 26, 28)]
    
    ORDINAL_COLORS_5 = [QColor.fromRgb(178, 223, 138),    # greens - already using for set stuff
                        QColor.fromRgb(51, 160, 44)]
    
    A = 0
    B = 1
    
    LEVEL_OPTIONS = {'1 Generation':1,
                     '2 Generations':2,
                     '3 Generations':3,
                     'All Generations':float('inf')}
    LEVEL_OPTION_ORDER = ['1 Generation',
                          '2 Generations',
                          '3 Generations',
                          'All Generations']
    
    ADDITION_ITERATOR_ORDER = ['Direct Ancestors',
                               'Direct Descendants',
                               'Ascend',
                               'Descend',
                               'All Directions']
    
    def __init__(self, ped):
        self.highlightedNode = None
        self.highlightedHistory = None
        self.overlaidAttribute = None
        self.highlightedPath = []
        self.aHistoryID = None
        self.bHistoryID = None
        self.aSet = set()
        self.bSet = set()
        self.abIntersection = set()
        self.filters = {}
        self.history = networkx.DiGraph()
        self.prefs = AppPreferences()
        
        self.scatterX = None
        self.scatterY = None
        
        self.historyCounter = 0
        
        self.ped = ped
        self.headers = [self.ped.REQUIRED_KEYS['personID']]
        self.headers.extend(self.ped.extraNodeAttributes)
        for h in self.headers:
            self.filters[h] = AttributeFilter(self.ped.attrDetails[h], self)
        
        self.components = set()
        
        self.additionIterators = {'Direct Ancestors':self.ped.iterUp,
                                  'Direct Descendants':self.ped.iterDown,
                                  'Ascend':self.ped.iterUpWithSpouses,
                                  'Descend':self.ped.iterDownWithSpouses,
                                  'All Directions':self.ped.iterFrom}
    
    def registerComponent(self, c):
        self.components.add(c)
    
    ##### Utility functions #####
    
    @staticmethod
    def blend(color1, color2, percentColor1=0.5):
        percentColor2 = 1.0-percentColor1
        
        # Convert from QColor to lab
        c1Alpha = color1.alpha()
        color1 = RGBColor(color1.red(),color1.green(),color1.blue()).convert_to('lab')
        c2Alpha = color2.alpha()
        color2 = RGBColor(color2.red(),color2.green(),color2.blue()).convert_to('lab')
        
        # Interpolate the colors in lab space
        result = LabColor(color1.lab_l*percentColor1+color2.lab_l*percentColor2,
                          color1.lab_a*percentColor1+color2.lab_a*percentColor2,
                          color1.lab_b*percentColor1+color2.lab_b*percentColor2)
        resultAlpha = c1Alpha*percentColor1 + c2Alpha*percentColor2
        
        # Convert back to QColor
        result = result.convert_to('rgb')
        return QColor.fromRgba(result.rgb_r,result.rgb_g,result.rgb_b,resultAlpha)
    
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
        if self.overlaidAttribute == None:
            fill = AppState.MISSING_COLOR
        else:
            fill = self.getColorForValue(self.ped.getAttribute(personID,self.overlaidAttribute,None), self.overlaidAttribute, alternate)
        if personID == self.highlightedNode:
            stroke = AppState.HIGHLIGHT_COLOR
            showFan = True
        else:
            stroke = AppState.BORDER_COLOR
        return (fill,stroke,showFan)
    
    def getFanColor(self, peopleIDs, alternate=1):
        # TODO
        pass
    
    def getPathColor(self, source, target):
        for s,t in self.highlightedPath:
            if (s == source and t == target) or (s == target and t == source):
                return AppState.HIGHLIGHT_COLOR
        return AppState.MISSING_COLOR
    
    def getHistoryPeople(self, historyID):
        if historyID == None or not self.history.node.has_key(historyID):
            return set()
        else:
            return self.history.node[historyID]['people']
    
    ##### State modification functions #####
    
    def highlightAnIndividual(self, n):
        previous = self.highlightedNode
        self.highlightedNode = n
        for c in self.components:
            c.notifyHighlightAnIndividual(previous, n)
    
    def showIndividualDetails(self, n):
        for c in self.components:
            c.notifyShowIndividualDetails(n)
    
    def performUnion(self):
        self.addPedigree(self.aSet.union(self.bSet), parentIDs=[self.aHistoryID,self.bHistoryID])
    
    def performIntersection(self):
        self.addPedigree(self.abIntersection, parentIDs=[self.aHistoryID,self.bHistoryID])
    
    def expand(self, person, peopleToAdd):
        parentHistoryID = None
        if person in self.abIntersection:
            self.performUnion()
            parentHistoryID = self.aHistoryID
        elif person in self.aSet:
            parentHistoryID = self.aHistoryID
        elif person in self.bSet:
            parentHistoryID = self.bHistoryID
        newSet = self.getHistoryPeople(parentHistoryID).union(peopleToAdd)
        self.addPedigree(newSet,[parentHistoryID])
    
    def snip(self, person, directions):
        parentHistoryID = None
        if person in self.abIntersection:
            self.performUnion()
            parentHistoryID = self.aHistoryID
        elif person in self.aSet:
            parentHistoryID = self.aHistoryID
        elif person in self.bSet:
            parentHistoryID = self.bHistoryID
        newSet = self.getHistoryPeople(parentHistoryID).discard(self.ped.iterFrom(person,directions,level=1,skipFirst=True))
        newSet = self.ped.getConnectedComponent(person,newSet)
        self.addPedigree(newSet,[parentHistoryID])
    
    def addPedigree(self, newPeopleSet, parentIDs=None):
        newID = self.historyCounter
        self.historyCounter += 1
        self.history.add_node(newID,{'people':newPeopleSet})
        
        if parentIDs != None:
            for parentID in parentIDs:
                assert self.history.node.has_key(parentID)
                # TODO: self.history.node[parentID]['preview'] = ?
                self.history.add_edge(parentID,newID)
            
            if self.aHistoryID in parentIDs:
                if self.bHistoryID in parentIDs:
                    self.changePedigreeB(None)
                self.changePedigreeA(newID)
            elif self.bHistoryID in parentIDs:
                self.changePedigreeB(newID)
        
        return newID
    
    def changePedigreeA(self, newID):
        previousID = self.aHistoryID
        if newID == None:
            if self.bHistoryID != None:
                newID = self.bHistoryID
                self.changePedigreeB(None)
            else:
                self.aSet = set()
                self.abIntersection = set()
                self.aHistoryID = None
                for c in self.components:
                    c.notifyChangePedigreeA(previousID, newID)
                return
        assert self.history.node.has_key(newID)
        self.aSet = self.history.node[newID]['people']
        self.abIntersection = self.aSet.intersection(self.bSet)
        self.aHistoryID = newID
        
        for c in self.components:
            c.notifyChangePedigreeA(previousID, newID)
    
    def changePedigreeB(self, newID):
        previousID = self.bHistoryID
        if newID == None:
            self.bSet = set()
            self.abIntersection = set()
            self.bHistoryID = None
        else:
            assert self.history.node.has_key(newID)
            self.bSet = self.history.node[newID]['people']
            self.abIntersection = self.aSet.intersection(self.bSet)
            self.bHistoryID = newID
        
        for c in self.components:
            c.notifyChangePedigreeA(previousID, newID)
    
    def higlightHistory(self, highlightedID):
        previous = self.highlightedHistory
        self.highlightedHistory = highlightedID
        for c in self.components:
            c.notifyHighlightHistory(previous,highlightedID)
    
    def changeOverlay(self, attr):
        previous = self.overlaidAttribute
        self.overlaidAttribute = attr
        for c in self.components:
            c.notifyChangeOverlay(previous, attr)
    
    def changeFilter(self):
        pass    # TODO
    
    def showScatterplot(self, attr1, attr2):
        prev1 = self.scatterX
        prev2 = self.scatterY
        self.scatterX = attr1
        self.scatterY = attr2
        for c in self.components:
            c.notifyShowScatterplot(prev1,prev2,attr1,attr2)
    
    def addPathTarget(self, person):
        pass    # TODO
    
    def removePathTarget(self, person):
        pass    # TODO
    
    def highlightPath(self, person1, person2):
        pass    # TODO
    
    def binColors(self, binningOn=True):
        self.prefs.binColors = binningOn
        for c in self.components:
            c.notifyChangePreferences()
    
    ##### Common context menus #####
    
    def showIndividualContextMenu(self, person):
        actionLookup = {}
        
        m = QMenu()
        actionLookup['Show Details'] = m.addAction('Show Details')
        # TODO: Add to / remove from path targets
        m.addSeparator()
        
        a = m.addMenu('Set A as')
        b = m.addMenu('Set B as')
        for label1 in AppState.ADDITION_ITERATOR_ORDER:
            a2 = a.addMenu(label1)
            b2 = b.addMenu(label1)
            for label2 in AppState.LEVEL_OPTION_ORDER:
                actionLookup[('Set A as',
                              self.additionIterators[label1],
                              AppState.LEVEL_OPTIONS[label2])] = a2.addAction(label2)
                actionLookup[('Set B as',
                              self.additionIterators[label1],
                              AppState.LEVEL_OPTIONS[label2])] = b2.addAction(label2)
        
        m.addSeparator()
        
        actionLookup['Trim Parents'] = m.addAction('Trim Parents')
        actionLookup['Trim Spouses'] = m.addAction('Trim Spouses')
        actionLookup['Trim Children'] = m.addAction('Trim Children')
        if not person in self.aSet and not person in self.bSet:
            actionLookup['Trim Parents'].setDisabled(True)
            actionLookup['Trim Spouses'].setDisabled(True)
            actionLookup['Trim Children'].setDisabled(True)
        
        m.addSeparator()
        
        for label1 in AppState.ADDITION_ITERATOR_ORDER:
            temp = m.addMenu('Expand '+label1)
            for label2 in AppState.LEVEL_OPTION_ORDER:
                actionLookup[('Expand',
                              self.additionIterators[label1],
                              AppState.LEVEL_OPTIONS[label2])] = temp.addAction(label2)
        
        choice = m.exec_(QCursor.pos())
        
        if choice != None:
            for menus,action in actionLookup.iteritems():
                if action == choice:
                    if menus == 'Show Details':
                        self.showIndividualDetails(person)
                    elif menus == 'Trim Parents':
                        self.snip(person, [self.ped.CHILD_TO_PARENT])
                    elif menus == 'Trim Spouses':
                        self.snip(person, [self.ped.HUSBAND_TO_WIFE,
                                           self.ped.WIFE_TO_HUSBAND])
                    elif menus == 'Trim Children':
                        self.snip(person, [self.ped.PARENT_TO_CHILD])
                    else:
                        assert isinstance(menus,tuple)
                        newSet = set(menus[1](person,level=menus[2]))
                        if menus[0] == 'Set A as':
                            historyID = self.addPedigree(newSet)
                            self.changePedigreeA(historyID)
                        elif menus[0] == 'Set B as':
                            historyID = self.addPedigree(newSet)
                            self.changePedigreeB(historyID)
                        elif menus[0] == 'Expand':
                            self.expand(person, newSet)
                    break
    
    def showHistoryContextMenu(self, historyID):
        pass
    
    def showAttributeMenu(self, attribute):
        m = QMenu()
        m.addAction('Overlay/Filter')
        c = m.addMenu('Compare to')
        for h in self.headers:
            c.addAction(h)
        m.addAction('Sort...')
        choice = m.exec_(QCursor.pos())
        
        if choice != None:
            choice = choice.text()
            if choice == 'Overlay/Filter':
                self.changeOverlay(attribute)
            elif choice == 'Sort...':
                # TODO
                pass
            else:
                self.showScatterplot(choice,attribute)
    
    def showSpreadsheetMaintenanceMenu(self):
        pass