'''
Created on Apr 3, 2013

@author: Alex Bigelow
'''
import sys, random, networkx
from PySide.QtGui import QApplication, QGraphicsScene, QGraphicsItem, QPen, QBrush, QColor, QPainterPath, QTableWidget, QTableWidgetItem, QPainter, QHeaderView
from PySide.QtCore import Qt, QFile, QRectF, QTimer
from PySide.QtUiTools import QUiLoader

window = None
corpses = set()

OVERLAY_ATTRIBUTE = None

BOTTOM = 500
RIGHT = 1900

class fadeableGraphicsItem(QGraphicsItem):
    SPEED = 0.05
    HIDDEN_OPACITY = 0.25
    
    def __init__(self):
        QGraphicsItem.__init__(self)
        self.dead = False
        self.hiding = False
        self.killed = False
        
        self.fadingIn = True
        self.fadingOut = False
        self.opacity = 0.0
    
    def updateValues(self):
        if self.fadingIn:
            self.opacity += fadeableGraphicsItem.SPEED
            if self.opacity >= 1.0:
                self.opacity = 1.0
                self.fadingIn = False
        elif self.fadingOut:
            self.opacity -= fadeableGraphicsItem.SPEED
            if self.hiding:
                if self.opacity <= fadeableGraphicsItem.HIDDEN_OPACITY:
                    self.opacity = fadeableGraphicsItem.HIDDEN_OPACITY
                    self.fadingOut = False
            elif self.killed:
                if self.opacity <= 0.0:
                    self.opacity = 0.0
                    self.fadingOut = False
                    self.dead = True
    
    def hide(self):
        if self.killed:
            return
        self.hiding = True
        self.fadingOut = True
    
    def show(self):
        self.hiding = False
        self.fadingIn = True
    
    def kill(self):
        self.hiding = False
        self.killed = True
        self.fadingIn = False
        self.fadingOut = True
    
    def revive(self):
        self.dead = False
        self.killed = False
        if not self.hiding:
            self.fadingOut = False
            self.fadingIn = True
        else:
            self.fadingOut = True
            self.fadingIn = False

class edge(fadeableGraphicsItem):
    HORIZONTAL_FORCE = 0.005
    VERTICAL_FORCE = 0.03
    
    MARRIAGE_PEN = QPen(Qt.lightGray, 2, Qt.DotLine)
    GENETIC_PEN = QPen(Qt.darkGray, 1.5)
    
    MARRIAGE = 0
    GENETIC = 1
    
    def __init__(self, source, target, edgeType):
        fadeableGraphicsItem.__init__(self)
        self.source = source
        self.target = target
        self.edgeType = edgeType
        self.pen = edge.MARRIAGE_PEN if edgeType == edge.MARRIAGE else edge.GENETIC_PEN
    
    def boundingRect(self):
        return QRectF(self.source.x(),self.source.y(),self.target.x(),self.target.y())
    
    def paint(self, painter, option, widget=None):
        if not self.dead:
            painter.setPen(self.pen)
            painter.setOpacity(self.opacity)
            painter.drawLine(self.source.x(),self.source.y(),self.target.x(),self.target.y())
    
    def getHorizontalForceOn(self, node):
        if node == self.source:
            return edge.HORIZONTAL_FORCE*(self.target.x() - self.source.x())
        else:
            return edge.HORIZONTAL_FORCE*(self.source.x() - self.target.x())
    
    def getVerticalForceOn(self, node):
        if self.edgeType != edge.MARRIAGE:
            return 0
        if node == self.source:
            return edge.VERTICAL_FORCE*(self.target.y() - self.source.y())
        else:
            return edge.VERTICAL_FORCE*(self.source.y() - self.target.y())

class node(fadeableGraphicsItem):
    MALE = 'M'
    FEMALE = 'F'
    
    DEFAULT_PEN = QPen(Qt.black, 1)
    HIGHLIGHT_PEN = QPen(Qt.black, 5)
    
    DEFAULT_BRUSH = QBrush(Qt.darkGray)
    CATEGORICAL_BRUSHES = [QColor(253, 191, 111),
                           QColor(255, 127, 0),
                           QColor(202, 178, 214),
                           QColor(106, 61, 154),
                           QColor(255, 255, 153),
                           QColor(166, 206, 227),
                           QColor(31, 120, 180),
                           QColor(178, 223, 138),
                           QColor(51, 160, 44),
                           QColor(251, 154, 153),
                           QColor(227, 26, 28)]
    SIZE = 12
    FAN_SIZE = 36
    FAN_PEN = QPen(Qt.black, 0)
    FAN_BRUSH = QBrush(Qt.darkGray)
    FAN_OPACITY = 0.5
    
    GENERATION_FORCE = 0.015
    REPULSION_FORCE = 0.005
    MAX_ENERGY = 1.0
    ENERGY_DECAY = 0.0001
    ENERGY_SWAP_THRESHOLD = 0.1
    
    def __init__(self, personID, panel, sex, startingX = None, startingY = None):
        fadeableGraphicsItem.__init__(self)
        self.setAcceptHoverEvents(True)
        
        self.personID = personID
        self.panel = panel
        
        self.sex = sex
        
        self.allParents = 0
        self.allChildren = 0
        self.allSpouses = 0
        
        self.hiddenParents = 0
        self.hiddenChildren = 0
        self.hiddenSpouses = 0
        
        self.verticalTarget = 0
        self.energy = node.MAX_ENERGY
        self.dx = 0.0
        self.dy = 0.0
        
        self.ignoreForces = False
        self.highlighted = False
        
        # start off with random positions; TODO: figure out bounds
        if startingX == None:
            startingX = random.randint(0,RIGHT)
        if startingY == None:
            startingY = random.randint(0,BOTTOM)
        self.setX(startingX)
        self.setY(startingY)
        
    def boundingRect(self):
        radius = node.FAN_SIZE*0.5
        return QRectF(-radius,-radius,node.FAN_SIZE,node.FAN_SIZE)
    
    def paint(self, painter, option, widget=None):
        # Center glyph
        radius = node.SIZE*0.5
        if self.highlighted:
            self.paintFan(painter)
            painter.setPen(node.HIGHLIGHT_PEN)
        else:
            painter.setPen(node.DEFAULT_PEN)
        painter.setOpacity(self.opacity)
        
        pOrC = self.panel.getPorC(self.personID)
        if pOrC == None:
            brush = node.DEFAULT_BRUSH
        elif isinstance(pOrC,float):
            brush = QBrush(QColor(255*pOrC,0,0))
        else:
            brush = node.CATEGORICAL_BRUSHES[pOrC]
        
        if self.sex == node.MALE:
            painter.fillRect(-radius,-radius,node.SIZE,node.SIZE,brush)
            #painter.drawRect(-radius,-radius,node.SIZE,node.SIZE)
        elif self.sex == node.FEMALE:
            path = QPainterPath()
            path.addEllipse(-radius,-radius,node.SIZE,node.SIZE)
            painter.fillPath(path,brush)
            #painter.drawPath(path)
        else:
            raise Exception('Unknown sex.')
    
    def paintFan(self, painter):
        painter.setOpacity(min(self.opacity,node.FAN_OPACITY))
        outerRadius = node.FAN_SIZE*0.5
        innerRadius = node.SIZE*0.5
        
        # Parent fan
        path = QPainterPath()
        
        if self.allParents == 0:
            pass
        elif self.hiddenParents > 0:
            # point out
            path.moveTo(-innerRadius,-innerRadius)
            path.lineTo(0,-outerRadius)
            path.lineTo(innerRadius,-innerRadius)
            path.lineTo(-innerRadius,-innerRadius)
        else:
            # point in
            path.moveTo(-innerRadius,-outerRadius)
            path.lineTo(0,-innerRadius)
            path.lineTo(innerRadius,-outerRadius)
            path.lineTo(-innerRadius,-outerRadius)
        painter.fillPath(path,node.FAN_BRUSH)
        
        # Marriage fans
        path1 = QPainterPath()
        path2 = QPainterPath()
        
        if self.allSpouses == 0:
            pass
        elif self.hiddenSpouses > 0:
            # point out
            path1.moveTo(-innerRadius,-innerRadius)
            path1.lineTo(-outerRadius,0)
            path1.lineTo(-innerRadius,innerRadius)
            path1.lineTo(-innerRadius,-innerRadius)
            
            path2.moveTo(innerRadius,-innerRadius)
            path2.lineTo(outerRadius,0)
            path2.lineTo(innerRadius,innerRadius)
            path2.lineTo(innerRadius,-innerRadius)
        else:
            # point in
            path1.moveTo(-outerRadius,-innerRadius)
            path1.lineTo(-innerRadius,0)
            path1.lineTo(-outerRadius,innerRadius)
            path1.lineTo(-outerRadius,-innerRadius)
            
            path2.moveTo(outerRadius,-innerRadius)
            path2.lineTo(innerRadius,0)
            path2.lineTo(outerRadius,innerRadius)
            path2.lineTo(outerRadius,-innerRadius)
        painter.fillPath(path1,node.FAN_BRUSH)
        painter.fillPath(path2,node.FAN_BRUSH)
        
        # Child fan
        path = QPainterPath()
        
        if self.allChildren == 0:
            pass
        elif self.hiddenChildren > 0:
            # point out
            path.moveTo(-innerRadius,innerRadius)
            path.lineTo(0,outerRadius)
            path.lineTo(innerRadius,innerRadius)
            path.lineTo(-innerRadius,innerRadius)
        else:
            # point in
            path.moveTo(-innerRadius,outerRadius)
            path.lineTo(0,innerRadius)
            path.lineTo(innerRadius,outerRadius)
            path.lineTo(-innerRadius,outerRadius)
        painter.fillPath(path,node.FAN_BRUSH)
    
    def hoverEnterEvent(self, event):
        self.panel.highlight(self.personID)
    
    def hoverLeaveEvent(self, event):
        self.panel.highlight(None)
    
    def mousePressEvent(self, event):
        self.grabMouse()
        self.ignoreForces = True
    
    def mouseMoveEvent(self, event):
        self.setPos(event.scenePos())
        # As moving a node will cause disruption, allow me (and consequently my neighbors) to move faster
        self.energy = node.MAX_ENERGY
    
    def mouseReleaseEvent(self, event):
        self.ungrabMouse()
        self.ignoreForces = False
        self.dx = 0
        self.dy = 0
        innerRadius = node.SIZE/2
        x,y = event.pos().toTuple()
        if x > -innerRadius and x < innerRadius:
            if y < -innerRadius:
                self.panel.expandOrCollapse(self,pedigreePanel.UP)
            elif y > innerRadius:
                self.panel.expandOrCollapse(self,pedigreePanel.DOWN)
        elif (x < -innerRadius or x > innerRadius) and y > -innerRadius and y < innerRadius:
            self.panel.expandOrCollapse(self,pedigreePanel.HORIZONTAL)
        
    def updateValues(self, neighbors):
        # Average every neighbor's energy with my own, then decay it a little
        fadeableGraphicsItem.updateValues(self)
        for n in neighbors:
            self.energy += n.energy
        self.energy = max(0,(self.energy/(len(neighbors)+1)-node.ENERGY_DECAY))
        self.moveBy(self.dx,self.dy)
    
    def applyForces(self, connectedEdges, generation, leftBound, rightBound):
        if self.ignoreForces:
            return
        
        dx0 = self.dx
        dy0 = self.dy
        
        # Vertical spring toward target
        self.dy = (self.verticalTarget-self.y())*node.GENERATION_FORCE
        
        # Pull from edges
        for e in connectedEdges:
            self.dx += e.getHorizontalForceOn(self)
            self.dy += e.getVerticalForceOn(self)
        
        # Push from the closest neighbors in the same generation
        mx = self.x()
        for r in generation:
            ox = r.x()
            if ox < mx:
                leftBound = max(ox,leftBound)
            elif ox > mx:
                rightBound = min(ox,rightBound)
        if rightBound-mx <= node.SIZE or mx-leftBound <= node.SIZE:
            # Shoot, we're overlapping with someone else... is our energy still high?
            if self.energy > node.ENERGY_SWAP_THRESHOLD:
                # Accelerate away
                if rightBound-mx > mx-leftBound:
                    distance = max(node.SIZE,mx-leftBound)**2
                else:
                    distance = -max(node.SIZE,rightBound-mx)**2
            else:
                # Otherwise, try swapping places and boosting our energy a little
                if rightBound-mx > mx-leftBound:
                    distance = -max(node.SIZE,rightBound-mx)**2
                else:
                    distance = max(node.SIZE,mx-leftBound)**2
                self.energy += node.ENERGY_SWAP_THRESHOLD
        else:
            distance = (leftBound+rightBound)*0.5-mx
        self.dx += node.REPULSION_FORCE*distance
        
        # If acceleration is zero, squash annoying tiny forces
        if self.dy - dy0 == 0 and abs(self.dy) < 0.2:
            self.dy = 0
        if self.dx - dx0 == 0 and abs(self.dx) < 0.2:
            self.dx = 0
        
        self.dx *= self.energy
        self.dy *= self.energy

class pedigreePanel:
    FRAME_DURATION = 1000/60 # 60 FPS
    
    UP = 0
    HORIZONTAL = 1
    DOWN = 2
    
    def __init__(self, view, ped):
        self.view = view
        self.ped = ped
        self.g = networkx.Graph()
        
        self.generations = {}
        self.minGen = None
        self.maxGen = None
        
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        
        self.timer = QTimer(self.view)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(pedigreePanel.FRAME_DURATION)
        
        self.highlighted = None
    
    def getPorC(self, personID):
        global OVERLAY_ATTRIBUTE
        return self.ped.getAttributeProportionOrClass(personID,OVERLAY_ATTRIBUTE)
    
    def highlight(self, person):
        if self.highlighted != person:
            if self.highlighted != None and self.g.node.has_key(self.highlighted) and not self.g.node[self.highlighted]['item'].dead:
                self.g.node[self.highlighted]['item'].highlighted = False
            self.highlighted = person
            if self.highlighted != None and self.g.node.has_key(self.highlighted) and not self.g.node[self.highlighted]['item'].dead:
                self.g.node[self.highlighted]['item'].highlighted = True
    
    def addPeople(self, people, direction = None):
        global corpses
        # Create the node objects, update the number of generations
        for p in people:
            if self.g.node.has_key(p):
                n = self.g.node[p]['item']
                n.revive()
            else:
                startingX = None
                startingY = None
                if direction == pedigreePanel.UP:
                    startingY = 0
                elif direction == pedigreePanel.HORIZONTAL:
                    startingX = 0
                elif direction == pedigreePanel.DOWN:
                    startingY = BOTTOM
                
                n = node(p,self,self.ped.getAttribute(p,'sex','?'), startingX, startingY)
                n.allParents,n.allSpouses,n.allChildren = self.ped.countNuclear(p)
                n.setZValue(1)
                self.g.add_node(p, {'item':n})
                self.scene.addItem(n)
        # Add links to other people that are in the pedigree
        for p in people:
            for p2,t in self.ped.iterNuclear(p):
                if self.g.node.has_key(p2):
                    if self.g.edge[p].has_key(p2):
                        e = self.g.edge[p][p2]['item']
                        e.revive()
                    else:
                        e = None
                        if t == self.ped.CHILD_TO_PARENT or t == self.ped.PARENT_TO_CHILD:
                            e = edge(self.g.node[p]['item'],self.g.node[p2]['item'],edge.GENETIC)
                        else:
                            e = edge(self.g.node[p]['item'],self.g.node[p2]['item'],edge.MARRIAGE)
                        e.setZValue(0)
                        self.g.add_edge(p, p2, {'item':e})
                        self.scene.addItem(e)
        self.refreshHiddenCounts()
        self.refreshGenerations()
        corpses = set() # painting happens in the same thread addPeople is in... we only want to release dead QGraphicsItems every once in a while
    
    def expandOrCollapse(self, item, direction):
        if item.dead:
            return
        if direction == pedigreePanel.UP:
            if item.allParents == 0:
                return
            elif item.hiddenParents > 0:
                self.addPeople(set(self.ped.iterParents(item.personID)),pedigreePanel.UP)
            else:
                self.discardPeople(set(self.ped.iterParents(item.personID)))
                self.cleanUp(item.personID)
        elif direction == pedigreePanel.HORIZONTAL:
            if item.allSpouses == 0:
                return
            elif item.hiddenSpouses > 0:
                self.addPeople(set(self.ped.iterSpouses(item.personID)),pedigreePanel.HORIZONTAL)
            else:
                self.discardPeople(set(self.ped.iterSpouses(item.personID)))
                self.cleanUp(item.personID)
        elif direction == pedigreePanel.DOWN:
            if item.allChildren == 0:
                return
            elif item.hiddenChildren > 0:
                self.addPeople(set(self.ped.iterChildren(item.personID)),pedigreePanel.DOWN)
            else:
                self.discardPeople(set(self.ped.iterChildren(item.personID)))
                self.cleanUp(item.personID)
    
    def cleanUp(self, person):
        # throw away any connected components that aren't connected to person
        nodesToRemove = set(self.g.node.iterkeys())
        nodesToKeep = set()
        
        # Iterate down then up BFS style
        toVisit = [person]
        while len(toVisit) > 0:
            p = toVisit.pop(0)
            if not p in nodesToKeep:
                nodesToKeep.add(p)
                nodesToRemove.discard(p)
                for p2 in self.g.edge[p].iterkeys():
                    if not self.g.node[p2]['item'].dead and not self.g.node[p2]['item'].killed:
                        toVisit.append(p2)
        
        self.discardPeople(nodesToRemove)
    
    def refreshHiddenCounts(self):
        for person in self.g.node.iterkeys():
            self.g.node[person]['item'].hiddenParents = 0
            self.g.node[person]['item'].hiddenChildren = 0
            self.g.node[person]['item'].hiddenSpouses = 0
            for p,t in self.ped.iterNuclear(person):
                if self.g.node.has_key(p) and not self.g.node[p]['item'].killed:
                    continue
                elif t == self.ped.PARENT_TO_CHILD:
                    self.g.node[person]['item'].hiddenChildren += 1
                elif t == self.ped.CHILD_TO_PARENT:
                    self.g.node[person]['item'].hiddenParents += 1
                else:
                    self.g.node[person]['item'].hiddenSpouses += 1
    
    def discardPeople(self, people):
        # Start the time bombs
        for p in people:
            if not self.g.edge.has_key(p):
                continue
            for attrs in self.g.edge[p].itervalues():
                attrs['item'].kill()
            self.g.node[p]['item'].kill()
    
    def removeEveryone(self):
        for source,target in self.g.edges():
            self.g.edge[source][target]['item'].kill()
        for attrs in self.g.node.itervalues():
            attrs['item'].kill()
    
    def refreshGenerations(self):
        self.generations = {}
        self.minGen = None
        self.maxGen = None
        
        for p in self.g.node.iterkeys():
            gen = self.ped.getAttribute(p,'generation',0)
            
            if self.minGen == None:
                self.minGen = gen
                self.maxGen = gen
            else:
                self.minGen = min(self.minGen,gen)
                self.maxGen = max(self.maxGen,gen)
            
            if not self.generations.has_key(gen):
                self.generations[gen] = set()
            self.generations[gen].add(p)
        
        if self.minGen == None:
            return
        
        bottom = BOTTOM    # TODO: get this size differently somehow...
        offset = node.SIZE*0.5 # center-based drawing
        increment = bottom / (max(self.maxGen-self.minGen+1,2))
        
        for p,attrs in self.g.node.iteritems():
            n = attrs['item']
            if not n.dead:
                slot = self.maxGen - self.ped.getAttribute(p,'generation',self.maxGen) - 1
                self.g.node[p]['item'].verticalTarget = bottom - slot*increment - offset
    
    def updateValues(self):
        # Update opacity values, positions for this frame
        nodesToRemove = set()
        edgesToRemove = set()
        for source, t in self.g.edge.iteritems():
            n = self.g.node[source]['item']
            myNeighbors = set()
            for target, attrs in t.iteritems():
                e = attrs['item']
                if not e.dead:
                    e.updateValues()
                    myNeighbors.add(self.g.node[target]['item'])
                else:
                    if not (target,source) in edgesToRemove:
                        edgesToRemove.add((source,target))
            if not n.dead:
                n.updateValues(myNeighbors)
            else:
                nodesToRemove.add(source)
        # Purge stuff we need to get rid of... start with edges
        existingItems = set(self.scene.items())
        for source,target in edgesToRemove:
            e = self.g.edge[source][target]['item']
            corpses.add(e)  # keep a reference to the item around until we know the main thread won't try to access it anymore (remember, this function is called from a timer)
            self.g.remove_edge(source, target)
            if e in existingItems:
                self.scene.removeItem(e)
        for p in nodesToRemove:
            n = self.g.node[p]['item']
            corpses.add(n)  # keep a reference to the item around until we know the main thread won't try to access it anymore (remember, this function is called from a timer)
            self.g.remove_node(p)
            if n in existingItems:
                self.scene.removeItem(n)
        self.refreshHiddenCounts()
        self.refreshGenerations()
        
        # Finally, prep the next update by applying forces
        for p,attrs in self.g.node.iteritems():
            connectedEdges = set(attrs['item'] for attrs in self.g.edge[p].itervalues())
            generationNodes = set(self.g.node[r]['item'] for r in self.generations[self.ped.getAttribute(p,'generation',self.maxGen)])
            attrs['item'].applyForces(connectedEdges,generationNodes,0,RIGHT)  # TODO: find these sizes differently somehow...
        self.scene.update()

class PythonTableWidgetItem(QTableWidgetItem):
    def __init__(self, sortKey):
        #call custom constructor with UserType item type
        QTableWidgetItem.__init__(self, str(sortKey), QTableWidgetItem.UserType)
        
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return self.sortKey < other.sortKey

class CustomHeader(QHeaderView):
    OVERLAY = Qt.red
    OVERLAY_OPACITY = 0.25
    
    def __init__(self, orientation, parent=None):
        QHeaderView.__init__(self, orientation, parent=None)
        self.setClickable(True)
        self.setMovable(True)
        self.overlayIndex = None
    
    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        QHeaderView.paintSection(self, painter, rect, logicalIndex)
        painter.restore()
        if logicalIndex == self.overlayIndex:
            painter.setOpacity(CustomHeader.OVERLAY_OPACITY)
            painter.fillRect(rect,CustomHeader.OVERLAY)
    
    def mouseReleaseEvent(self, event):
        lastOverlay = self.overlayIndex
        nextIndex = self.logicalIndex(self.visualIndexAt(event.pos().x()))
        
        if nextIndex == lastOverlay:
            self.overlayIndex = None
        else:
            self.overlayIndex = nextIndex
        
        self.parent().setOverlay(self.overlayIndex)
        
        if not lastOverlay == None:
            self.updateSection(lastOverlay)
        if not nextIndex == None:
            self.updateSection(nextIndex)
        
        QHeaderView.mouseReleaseEvent(self, event)

class TableWidget(QTableWidget):
    NORMAL_BG = QBrush(Qt.white)
    
    MOUSE_OVER_BG = QBrush(Qt.lightGray)
    
    MOUSE_META_BG = QBrush(Qt.gray)
    
    ACTIVE_BG = QBrush(Qt.darkGray)
    
    META_KEYS = [Qt.SHIFT,Qt.META,Qt.ALT,Qt.CTRL]
    
    def __init__(self, mainApp):
        QTableWidget.__init__(self)
        self.mainApp = mainApp
        
        self.headerObj = CustomHeader(Qt.Horizontal, self)
        self.setHorizontalHeader(self.headerObj)
        
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(True)
        
        self.numColumns = 0
        self.mousedRow = None
        self.activeIDs = set()
    
    def setOverlay(self, index):
        global OVERLAY_ATTRIBUTE
        if index == None:
            OVERLAY_ATTRIBUTE = index
        else:
            OVERLAY_ATTRIBUTE = self.horizontalHeaderItem(index).text()
    
    def setItem(self, row, column, item):
        QTableWidget.setItem(self,row,column,item)
        item.setBackground(TableWidget.NORMAL_BG)
        self.numColumns = max(column,self.numColumns)
    
    def mouseDoubleClickEvent(self, event):
        k = QApplication.keyboardModifiers()
        m = event.button()
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        if m == Qt.LeftButton:
            if k in TableWidget.META_KEYS:
                if currentID in self.activeIDs:
                    self.activeIDs.discard(currentID)
                    self.mainApp.detach(currentID)
                else:
                    self.activeIDs.add(currentID)
                    self.mainApp.intersect(currentID)
            else:
                self.activeIDs = set([currentID])
                self.mainApp.switch(currentID)
    
    def mouseMoveEvent(self, event):
        k = QApplication.keyboardModifiers()
        m = QApplication.mouseButtons()
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        # Don't mess with anything if the buttons are doing something
        if m == Qt.NoButton:
            # Wipe out old mouse actions
            if self.mousedRow != currentRow and self.mousedRow != None:
                    for c in xrange(self.numColumns+1):
                        self.item(self.mousedRow,c).setBackground(TableWidget.NORMAL_BG)
            # Set up new mouse actions
            self.mousedRow = currentRow
            brush = None
            if k in TableWidget.META_KEYS:
                brush = TableWidget.MOUSE_META_BG
                # TODO: handle meta interactions
            else:
                brush = TableWidget.MOUSE_OVER_BG
                self.mainApp.highlight(currentID)
            # Draw new mouse actions
            for c in xrange(self.numColumns+1):
                self.item(self.mousedRow,c).setBackground(brush)
    
    def leaveEvent(self, event):
        # Clean up mousing
        if self.mousedRow != None:
            for c in xrange(self.numColumns+1):
                self.item(self.mousedRow,c).setBackground(TableWidget.NORMAL_BG)
        self.mousedRow = None

class Vis:
    def __init__(self, ped):
        self.ped = ped
        
        self.loader = QUiLoader()
        infile = QFile("resources/vis.ui")
        infile.open(QFile.ReadOnly)
        self.window = self.loader.load(infile, None)
        infile.close()
        
        '''
        objects in self.window:
        
        QSplitter:
        lowSplitter
        
        QGraphicsView:
        plotView
        pedigreeView
        historyView
        '''
        # Add our custom table on the fly
        self.window.dataTable = TableWidget(self)
        self.window.lowSplitter.insertWidget(0,self.window.dataTable)
        self.window.lowSplitter.update()
        
        # Load up all the data into the spreadsheet
        self.headers = [self.ped.REQUIRED_KEYS['personID']]
        self.headers.extend(self.ped.extraNodeAttributes)
        self.window.dataTable.setColumnCount(len(self.headers))
        self.window.dataTable.setRowCount(len(self.ped.rowOrder))
        self.window.dataTable.setHorizontalHeaderLabels(self.headers)
        for r,p in enumerate(self.ped.rowOrder):
            self.window.dataTable.setItem(r,0,PythonTableWidgetItem(p))
            for c,a in enumerate(self.ped.extraNodeAttributes):
                self.window.dataTable.setItem(r,c+1,PythonTableWidgetItem(self.ped.getAttribute(p,a,None)))
        self.overlayAttribute = None
        
        # Set up the pedigree view
        self.pedigreeView = pedigreePanel(self.window.pedigreeView, self.ped)
        
        # Bind events
        self.window.dataTable.setMouseTracking(True)
        self.window.dataTable.viewport().setMouseTracking(True)
        
        self.window.showMaximized()
        #self.window.showFullScreen()
    
    def highlight(self, person):
        self.pedigreeView.highlight(person)
    
    def switch(self, person):
        oldSet = set(self.pedigreeView.g.node.iterkeys())
        newSet = set(self.ped.iterDown(person))
        
        self.pedigreeView.discardPeople(oldSet.difference(newSet))
        self.pedigreeView.addPeople(newSet.difference(oldSet))
    
    def previewIntersect(self, person):
        pass
    
    def intersect(self, person):
        pass
    
    def previewDetach(self, person):
        pass
    
    def detach(self, person):
        pass
    
def run(ped):
    app = QApplication(sys.argv)
    window = Vis(ped)
    return app.exec_()