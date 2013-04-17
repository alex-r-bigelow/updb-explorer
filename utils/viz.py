'''
Created on Apr 3, 2013

@author: Alex Bigelow
'''
import sys, math, random, networkx
from PySide.QtGui import QApplication, QGraphicsScene, QGraphicsItem, QPen, QBrush, QPainterPath, QTableWidget, QTableWidgetItem
from PySide.QtCore import Qt, QFile, QRectF, QTimer, QObject, QEvent
from PySide.QtUiTools import QUiLoader

window = None
corpses = set()

class fadeableGraphicsItem(QGraphicsItem):
    SPEED = 0.05
    def __init__(self):
        QGraphicsItem.__init__(self)
        self.dead = False
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
            if self.opacity <= 0.0:
                self.opacity = 0.0
                self.fadingOut = False
                self.dead = True
    
    def kill(self):
        self.fadingIn = False
        self.fadingOut = True
    
    def revive(self):
        self.dead = False
        self.fadingOut = False
        if self.opacity < 1.0:
            self.fadingIn = True

class edge(fadeableGraphicsItem):
    HORIZONTAL_FORCE = 0.005
    VERTICAL_FORCE = 0.03
    
    MARRIAGE_PEN = QPen(Qt.lightGray, 2, Qt.DotLine)
    GENETIC_PEN = QPen(Qt.darkGray, 2)
    
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
    UP = 'U'
    DOWN = 'D'
    LEFT = 'L'
    RIGHT = 'R'
    EXPANSIONSEXES = set([UP,DOWN,LEFT,RIGHT])
    
    DEFAULT_PEN = QPen(Qt.darkGray, 1)
    HIGHLIGHT_PEN = QPen(Qt.green, 4)
    
    DEFAULT_BRUSH = QBrush(Qt.darkGray)
    AFFECTED_BRUSH = QBrush(Qt.red)
    ANCESTOR_BRUSH = QBrush(Qt.black)
    
    SIZE = 15
    
    GENERATION_FORCE = 0.015
    REPULSION_FORCE = 0.01
    ENERGY_DECAY = 0.0001
    
    def __init__(self, personID, panel, sex, startingX = None, startingY = None):
        fadeableGraphicsItem.__init__(self)
        self.personID = personID
        self.panel = panel
        
        self.sex = sex
        
        self.verticalTarget = 0
        self.energy = 1.0
        self.dx = 0.0
        self.dy = 0.0
        
        self.ignoreForces = False
        
        # start off with random positions; TODO: figure out bounds
        if startingX == None:
            startingX = random.randint(0,1900)
        if startingY == None:
            startingY = random.randint(0,500)
        self.setX(startingX)
        self.setY(startingY)
        
        self.pen = node.DEFAULT_PEN
        self.brush = node.DEFAULT_BRUSH
    
    def boundingRect(self):
        stroke = self.pen.widthF()
        radius = node.SIZE*0.5 + stroke
        return QRectF(-radius,-radius,node.SIZE+stroke,node.SIZE+stroke)
    
    def paint(self, painter, option, widget=None):
        radius = node.SIZE*0.5
        painter.setPen(self.pen)
        painter.setOpacity(self.opacity)
        if self.sex == node.MALE:
            painter.fillRect(-radius,-radius,node.SIZE,node.SIZE,self.brush)
            painter.drawRect(-radius,-radius,node.SIZE,node.SIZE)
        elif self.sex == node.FEMALE:
            path = QPainterPath()
            path.addEllipse(-radius,-radius,node.SIZE,node.SIZE)
            painter.fillPath(path,self.brush)
            painter.drawPath(path)
        elif self.sex == node.UP:
            path = QPainterPath()
            path.moveTo(-radius,radius)
            path.lineTo(0,-radius)
            path.lineTo(radius,radius)
            path.lineTo(-radius,radius)
            painter.fillPath(path,self.brush)
            painter.drawPath(path)
        elif self.sex == node.DOWN:
            path = QPainterPath()
            path.moveTo(-radius,-radius)
            path.lineTo(0,radius)
            path.lineTo(radius,-radius)
            path.lineTo(-radius,-radius)
            painter.fillPath(path,self.brush)
            painter.drawPath(path)
        elif self.sex == node.LEFT:
            path = QPainterPath()
            path.moveTo(radius,-radius)
            path.lineTo(-radius,0)
            path.lineTo(radius,radius)
            path.lineTo(radius,-radius)
            painter.fillPath(path,self.brush)
            painter.drawPath(path)
        elif self.sex == node.RIGHT:
            path = QPainterPath()
            path.moveTo(-radius,-radius)
            path.lineTo(radius,0)
            path.lineTo(-radius,radius)
            path.lineTo(-radius,-radius)
            painter.fillPath(path,self.brush)
            painter.drawPath(path)
        else:
            raise Exception('Unknown sex.')
    
    def mousePressEvent(self, event):
        self.grabMouse()
        self.ignoreForces = True
    
    def mouseMoveEvent(self, event):
        self.setPos(event.scenePos())
        self.panel.highlight(self.personID)
        # As moving a node will cause disruption, allow me (and consequently my neighbors) to move faster
        self.energy = 1.0
    
    def mouseReleaseEvent(self, event):
        self.ungrabMouse()
        self.dx = 0
        self.dy = 0
        self.ignoreForces = False
        if self.sex in node.EXPANSIONSEXES:
            self.panel.expand(self.personID)
        
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
        if rightBound-leftBound <= node.SIZE:
            # Shoot, we're overlapping with someone else... try swapping places
            if rightBound-mx > mx-leftBound:
                distance = rightBound-mx+node.SIZE
            else:
                distance = leftBound-mx-node.SIZE
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
    
    def highlight(self, person):
        if self.highlighted != person:
            if self.highlighted != None and self.g.node.has_key(self.highlighted) and not self.g.node[self.highlighted]['item'].dead:
                self.g.node[self.highlighted]['item'].pen = node.DEFAULT_PEN
            self.highlighted = person
            if self.g.node.has_key(self.highlighted) and not self.g.node[self.highlighted]['item'].dead:
                self.g.node[self.highlighted]['item'].pen = node.HIGHLIGHT_PEN
    
    def expand(self, person):
        pass
    
    def addPeople(self, people, link=False):
        # Create the node objects, update the number of generations
        for p in people:
            if self.g.node.has_key(p):
                n = self.g.node[p]['item']
                n.revive()
            else:
                n = node(p,self,self.ped.getAttribute(p,'sex','?'), startingX = 0)
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
        self.refreshGenerations()
        corpses = set() # painting happens in the same thread addPeople is in... this releases objects taking up memory
    
    def removePeople(self, people):
        # Start the time bombs
        for p in people:
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
        
        bottom = 500    # TODO: get this size differently somehow...
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
            corpses.add(e)  # keep a reference to the item around until we know Qt won't try to access it any more
            self.g.remove_edge(source, target)
            if e in existingItems:
                self.scene.removeItem(e)
        for p in nodesToRemove:
            n = self.g.node[p]['item']
            corpses.add(n)  # keep a reference to the item around until we know Qt won't try to access it any more
            self.g.remove_node(p)
            if n in existingItems:
                self.scene.removeItem(n)
        self.refreshGenerations()
        
        # Finally, prep the next update by applying forces
        for p,attrs in self.g.node.iteritems():
            connectedEdges = set(attrs['item'] for attrs in self.g.edge[p].itervalues())
            generationNodes = set(self.g.node[r]['item'] for r in self.generations[self.ped.getAttribute(p,'generation',self.maxGen)])
            attrs['item'].applyForces(connectedEdges,generationNodes,0,1900)  # TODO: find these sizes differently somehow...
        self.scene.update()

class PythonTableWidgetItem(QTableWidgetItem):
    def __init__(self, sortKey):
        #call custom constructor with UserType item type
        QTableWidgetItem.__init__(self, str(sortKey), QTableWidgetItem.UserType)
        
        self.sortKey = sortKey

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return self.sortKey < other.sortKey

class TableWidget(QTableWidget):
    NORMAL_BG = QBrush(Qt.white)
    
    MOUSE_OVER_BG = QBrush(Qt.green)
    
    MOUSE_META_BG = QBrush(Qt.gray)
    
    ACTIVE_BG = QBrush(Qt.darkGray)
    
    META_KEYS = [Qt.SHIFT,Qt.META,Qt.ALT,Qt.CTRL]
    
    def __init__(self, mainApp):
        QTableWidget.__init__(self)
        self.mainApp = mainApp
        
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(True)
        
        self.numColumns = 0
        self.mousedRow = None
        self.activeIDs = set()
    
    def setItem(self, row, column, item):
        QTableWidget.setItem(self,row,column,item)
        item.setBackground(TableWidget.NORMAL_BG)
        self.numColumns = max(column,self.numColumns)
    
    def mouseReleaseEvent(self, event):
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

class Viz:
    def __init__(self, ped):
        self.ped = ped
        
        self.loader = QUiLoader()
        infile = QFile("utils/viz.ui")
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
        headers = [self.ped.REQUIRED_KEYS['personID']]
        headers.extend(self.ped.extraNodeAttributes)
        self.window.dataTable.setColumnCount(len(headers))
        self.window.dataTable.setRowCount(len(self.ped.rowOrder))
        self.window.dataTable.setHorizontalHeaderLabels(headers)
        for r,p in enumerate(self.ped.rowOrder):
            self.window.dataTable.setItem(r,0,PythonTableWidgetItem(p))
            for c,a in enumerate(self.ped.extraNodeAttributes):
                self.window.dataTable.setItem(r,c+1,PythonTableWidgetItem(self.ped.getAttribute(p,a,None)))
        
        # Set up the pedigree view
        self.pedigreeView = pedigreePanel(self.window.pedigreeView, self.ped)
        
        # Bind events
        self.window.dataTable.setMouseTracking(True)
        self.window.dataTable.viewport().setMouseTracking(True)
        
        #self.window.showMaximized()
        self.window.showFullScreen()
    
    def highlight(self, person):
        self.pedigreeView.highlight(person)
    
    def switch(self, person):
        oldSet = set(self.pedigreeView.g.node.iterkeys())
        newSet = set(self.ped.iterDownWithSpouses(person))
        
        self.pedigreeView.removePeople(oldSet.difference(newSet))
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
    window = Viz(ped)
    return app.exec_()