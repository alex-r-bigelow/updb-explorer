import random, math, pygraphviz
from PySide.QtGui import QGraphicsScene, QGraphicsItem, QPen, QBrush, QFont, QPainterPath
from PySide.QtCore import Qt, QRectF, QTimer
from app_state import AppComponent
from pedigree_data import Pedigree

class fadeableGraphicsItem(QGraphicsItem):
    OPACITY_SPEED = 0.05
    HIDDEN_OPACITY = 0.25
    SPATIAL_SPEED = 10
    
    def __init__(self, x, y):
        QGraphicsItem.__init__(self)
        self.hiding = False
        self.killed = False
        self.dead = False
        self.frozen = False
        
        self.opacity = 0.0
        self.targetX = x
        self.targetY = y
        self.setPos(x,y)
    
    def updateValues(self):
        if self.dead:
            self.opacity = 0.0
        elif self.killed:
            self.opacity = max(0.0,self.opacity-fadeableGraphicsItem.OPACITY_SPEED)
            if self.opacity == 0.0:
                self.dead = True
        elif self.frozen:
            return
        elif self.hiding:
            if self.opacity >= fadeableGraphicsItem.HIDDEN_OPACITY:
                self.opacity = max(fadeableGraphicsItem.HIDDEN_OPACITY,self.opacity-fadeableGraphicsItem.OPACITY_SPEED)
            else:
                self.opacity = min(fadeableGraphicsItem.HIDDEN_OPACITY,self.opacity+fadeableGraphicsItem.OPACITY_SPEED)
        else:
            self.opacity = min(1.0,self.opacity+fadeableGraphicsItem.OPACITY_SPEED)
        
        x = self.x()
        y = self.y()
        if x >= self.targetX:
            self.setX(max(self.targetX,x-fadeableGraphicsItem.SPATIAL_SPEED))
        else:
            self.setX(min(self.targetX,x+fadeableGraphicsItem.SPATIAL_SPEED))
        if y >= self.targetY:
            self.setY(max(self.targetY,y-fadeableGraphicsItem.SPATIAL_SPEED))
        else:
            self.setY(min(self.targetY,y+fadeableGraphicsItem.SPATIAL_SPEED))
    
    def hide(self):
        if self.killed:
            return
        self.hiding = True
    
    def show(self):
        self.hiding = False
    
    def kill(self):
        self.killed = True
    
    def forceDead(self):
        self.hiding = False
        self.killed = True
        self.dead = True
        self.opacity = 0.0
    
    def revive(self):
        self.dead = False
        self.killed = False
    
    def freeze(self):
        self.frozen = True
    
    def thaw(self):
        self.frozen = False

class node(fadeableGraphicsItem):
    INNER_RADIUS = 6
    OUTER_RADIUS = 18
    PARTIAL_OFFSET = 3
    STROKE_WEIGHT = 3
    FAN_OPACITY = 0.5
    SCISSOR_WEIGHT = 3
    
    UP = 0
    DOWN = 1
    HORIZONTAL = 2
    
    def __init__(self, personID, panel, startingX = None, startingY = None):
        if startingX == None:
            startingX = random.randint(0,panel.right)
        if startingY == None:
            startingY = random.randint(0,panel.bottom)
        fadeableGraphicsItem.__init__(self, startingX, startingY)
        self.setAcceptHoverEvents(True)
        
        self.personID = personID
        self.panel = panel
        
        self.allParents = 0
        self.allChildren = 0
        self.allSpouses = 0
        
        self.hiddenParents = 0
        self.hiddenChildren = 0
        self.hiddenSpouses = 0
        
        self.snipDirection = None
        
        self.setZValue(2)
    
    def boundingRect(self):
        radius = node.OUTER_RADIUS*0.5
        return QRectF(-radius,-radius,node.OUTER_RADIUS,node.OUTER_RADIUS)
    
    def drawScissors(self, painter):
        painter.setOpacity(1.0)
        painter.setPen(QPen(self.panel.appState.MISSING_COLOR,node.SCISSOR_WEIGHT))
        
        if self.snipDirection == node.UP:
            painter.drawLine(-node.INNER_RADIUS,-node.OUTER_RADIUS,node.INNER_RADIUS,-node.INNER_RADIUS)
            painter.drawLine(node.INNER_RADIUS,-node.OUTER_RADIUS,-node.INNER_RADIUS,-node.INNER_RADIUS)
        elif self.snipDirection == node.HORIZONTAL:
            painter.drawLine(-node.OUTER_RADIUS,-node.INNER_RADIUS,-node.INNER_RADIUS,node.INNER_RADIUS)
            painter.drawLine(-node.OUTER_RADIUS,node.INNER_RADIUS,-node.INNER_RADIUS,-node.INNER_RADIUS)
            painter.drawLine(node.OUTER_RADIUS,-node.INNER_RADIUS,node.INNER_RADIUS,node.INNER_RADIUS)
            painter.drawLine(node.OUTER_RADIUS,node.INNER_RADIUS,node.INNER_RADIUS,-node.INNER_RADIUS)
        elif self.snipDirection == node.DOWN:
            painter.drawLine(-node.INNER_RADIUS,node.OUTER_RADIUS,node.INNER_RADIUS,node.INNER_RADIUS)
            painter.drawLine(node.INNER_RADIUS,node.OUTER_RADIUS,-node.INNER_RADIUS,node.INNER_RADIUS)
    
    def drawFan(self, painter):
        painter.setOpacity(self.opacity*node.FAN_OPACITY)
        fill = self.panel.appState.MISSING_COLOR
        
        # Parent fan
        if self.hiddenParents > 0:
            path = QPainterPath()
            
            # point out
            path.moveTo(-node.INNER_RADIUS,-node.INNER_RADIUS)
            if self.hiddenParents < self.allParents:
                path.lineTo(-node.PARTIAL_OFFSET,-node.OUTER_RADIUS)
                path.lineTo(node.PARTIAL_OFFSET,-node.OUTER_RADIUS)
            else:
                path.lineTo(0,-node.OUTER_RADIUS)
            path.lineTo(node.INNER_RADIUS,-node.INNER_RADIUS)
            path.lineTo(-node.INNER_RADIUS,-node.INNER_RADIUS)
            painter.fillPath(path,fill)
        
        # Marriage fans
        if self.hiddenSpouses > 0:
            path1 = QPainterPath()
            path2 = QPainterPath()
            
            # point out
            path1.moveTo(-node.INNER_RADIUS,-node.INNER_RADIUS)
            if self.hiddenSpouses < self.allSpouses:
                path1.lineTo(-node.OUTER_RADIUS,-node.PARTIAL_OFFSET)
                path1.lineTo(-node.OUTER_RADIUS,node.PARTIAL_OFFSET)
            else:
                path1.lineTo(-node.OUTER_RADIUS,0)
            path1.lineTo(-node.INNER_RADIUS,node.INNER_RADIUS)
            path1.lineTo(-node.INNER_RADIUS,-node.INNER_RADIUS)
            
            path2.moveTo(node.INNER_RADIUS,-node.INNER_RADIUS)
            if self.hiddenSpouses < self.allSpouses:
                path1.lineTo(node.OUTER_RADIUS,-node.PARTIAL_OFFSET)
                path1.lineTo(node.OUTER_RADIUS,node.PARTIAL_OFFSET)
            else:
                path1.lineTo(node.OUTER_RADIUS,0)
            path2.lineTo(node.INNER_RADIUS,node.INNER_RADIUS)
            path2.lineTo(node.INNER_RADIUS,-node.INNER_RADIUS)
            
            painter.fillPath(path1,fill)
            painter.fillPath(path2,fill)
        
        # Child fan
        if self.hiddenChildren > 0:
            path = QPainterPath()
            
            # point out
            path.moveTo(-node.INNER_RADIUS,node.INNER_RADIUS)
            if self.hiddenParents < self.allParents:
                path.lineTo(-node.PARTIAL_OFFSET,node.OUTER_RADIUS)
                path.lineTo(node.PARTIAL_OFFSET,node.OUTER_RADIUS)
            else:
                path.lineTo(0,node.OUTER_RADIUS)
            path.lineTo(node.INNER_RADIUS,node.INNER_RADIUS)
            path.lineTo(-node.INNER_RADIUS,node.INNER_RADIUS)
            painter.fillPath(path,fill)
    
    def drawSquare(self, painter, stroke=None, fill=None):
        painter.setOpacity(self.opacity)
        if fill != None:
            painter.fillRect(-node.INNER_RADIUS,-node.INNER_RADIUS,node.INNER_RADIUS*2,node.INNER_RADIUS*2,fill)
        if stroke != None:
            painter.setPen(stroke)
            painter.drawRect(-node.INNER_RADIUS,-node.INNER_RADIUS,node.INNER_RADIUS*2,node.INNER_RADIUS*2)
    
    def drawCircle(self, painter, stroke=None, fill=None):
        painter.setOpacity(self.opacity)
        path = QPainterPath()
        path.addEllipse(-node.INNER_RADIUS,-node.INNER_RADIUS,node.INNER_RADIUS*2,node.INNER_RADIUS*2)
        if fill != None:
            painter.fillPath(path,fill)
        if stroke != None:
            painter.setPen(stroke)
            painter.drawPath(path)
    
    def paint(self, painter, option, widget=None):
        fill,stroke,showFan = self.panel.appState.getColors(self.personID)
        stroke = QPen(stroke,node.STROKE_WEIGHT)
        
        if showFan:
            self.drawFan(painter)
        
        if self.snipDirection != None:
            self.drawScissors(painter)
        
        # Center shape
        sex = self.panel.appState.ped.getAttribute(self.personID,'sex','?')
        if sex == 'M':
            self.drawSquare(painter, stroke, fill)
        elif sex == 'F':
            self.drawCircle(painter, stroke, fill)
        else:
            raise Exception('Unknown sex.')
    
    def hoverEnterEvent(self, event):
        self.panel.appState.highlightAnIndividual(self.personID)
    
    def hoverLeaveEvent(self, event):
        self.panel.appState.highlightAnIndividual(None)
    
    def mouseDoubleClickEvent(self, event):
        self.panel.appState.showIndividualDetails(self.personID)
    
    def mousePressEvent(self, event):
        self.grabMouse()
        self.freeze()
        x,y = event.pos().toTuple()
        if x > -node.OUTER_RADIUS \
        and x < node.OUTER_RADIUS \
        and y > -node.OUTER_RADIUS \
        and y < node.OUTER_RADIUS:
            if x > -node.INNER_RADIUS and x < node.INNER_RADIUS:
                if y < -node.INNER_RADIUS:
                    self.snipDirection = node.UP
                elif y > node.INNER_RADIUS:
                    self.snipDirection = node.DOWN
            elif (x < -node.INNER_RADIUS or x > node.INNER_RADIUS) \
            and y > -node.INNER_RADIUS \
            and y < node.INNER_RADIUS:
                self.snipDirection = node.HORIZONTAL
    
    def mouseMoveEvent(self, event):
        if self.snipDirection == None:
            self.setPos(event.scenePos())
    
    def mouseReleaseEvent(self, event):
        self.ungrabMouse()
        self.thaw()
        if self.snipDirection != None:
            # Only perform a snip action if we started and ended in the same area
            x,y = event.pos().toTuple()
            if x > -node.OUTER_RADIUS \
            and x < node.OUTER_RADIUS \
            and y > -node.OUTER_RADIUS \
            and y < node.OUTER_RADIUS:
                if x > -node.INNER_RADIUS and x < node.INNER_RADIUS:
                    if y < -node.INNER_RADIUS and self.snipDirection == node.UP:
                        self.panel.appState.snip(self.personID,[self.panel.ped.CHILD_TO_PARENT])
                    elif y > node.INNER_RADIUS and self.snipDirection == node.DOWN:
                        self.panel.appState.snip(self.personID,[self.panel.ped.PARENT_TO_CHILD])
                elif (x < -node.INNER_RADIUS or x > node.INNER_RADIUS) \
                and y > -node.INNER_RADIUS \
                and y < node.INNER_RADIUS \
                and self.snipDirection == node.HORIZONTAL:
                    self.panel.appState.snip(self.personID,[self.panel.ped.HUSBAND_TO_WIFE,
                                                            self.panel.ped.WIFE_TO_HUSBAND])
            self.snipDirection = None
        else:
            pass
            # TODO: reorder the nodes

class ghostNode(object):
    def __init__(self, parent, child):
        self.parent = parent
        self.child = child

class pedigreeSlice(fadeableGraphicsItem):
    OPACITY_PROPORTION = 0.5
    THICKNESS = 5
    
    def __init__(self, x, y, height, brush):
        fadeableGraphicsItem.__init__(self, x, y)
        self.height = height
        self.brush = brush
        self.setZValue(3)
    
    def boundingRect(self):
        return QRectF(-pedigreeSlice.THICKNESS*0.5,-self.height*0.5,pedigreeSlice.THICKNESS,self.height)
    
    def paint(self, painter, option, widget=None):
        painter.setOpacity(self.opacity*pedigreeSlice.OPACITY_PROPORTION)
        painter.fillRect(-pedigreeSlice.THICKNESS*0.5,-self.height*0.5,pedigreeSlice.THICKNESS,self.height,self.brush)

class edgeLayer(QGraphicsItem):
    def __init__(self, panel):
        QGraphicsItem.__init__(self)
        self.panel = panel
        self.setZValue(1)
    
    def boundingRect(self):
        return QRectF(0.0,0.0,self.panel.right,self.panel.bottom)
    
    def paint(self, painter, option, widget=None):
        painter.fillRect(0,0,self.panel.right,self.panel.bottom,self.panel.appState.BACKGROUND_COLOR)
        for a in self.panel.nodes.iterkeys():
            if self.panel.nodes[a].dead:
                continue
            for b,l in self.panel.appState.ped.iterNuclear(a):
                if not self.panel.nodes.has_key(b) or self.panel.nodes[b].dead:
                    continue
                color = self.panel.appState.getPathColor(a,b)
                if l == Pedigree.HUSBAND_TO_WIFE or l == Pedigree.WIFE_TO_HUSBAND:
                    pen = QPen(color, 1.5, Qt.DotLine)
                else:
                    pen = QPen(color, 1.5)
                painter.setPen(pen)
                # TODO: set opacity?
                painter.drawLine(self.panel.nodes[a].x(),self.panel.nodes[a].y(),
                                 self.panel.nodes[b].x(),self.panel.nodes[b].y())

class PedigreeComponent(AppComponent):
    FRAME_DURATION = 1000/60 # 60 FPS
    
    UP = 0
    HORIZONTAL = 1
    DOWN = 2
    
    def __init__(self, view, appState):
        self.view = view
        self.appState = appState
        self.appState.registerComponent(self)
        
        self.nodes = {}
        self.corpses = set()
        
        self.generations = {}
        self.generationOrder = []
        
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        # TODO: figure out these sizes differently...
        self.bottom = 400
        self.right = 1900
        
        self.edges = edgeLayer(self)
        self.scene.addItem(self.edges)
        self.aSlice = pedigreeSlice(self.right,self.bottom/2,self.bottom,self.appState.MISSING_COLOR)
        self.scene.addItem(self.aSlice)
        self.bSlice = pedigreeSlice(self.right,self.bottom/2,self.bottom,self.appState.MISSING_COLOR)
        self.scene.addItem(self.bSlice)
        
        # TODO: add some buttons for union, intersection, and closing A and B
        
        self.timer = QTimer(self.view)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(PedigreeComponent.FRAME_DURATION)
    
    def addCorpse(self,i):
        self.corpses.add(i)
    
    def dumpCorpses(self):
        self.corpses = set()
        
    def notifyChangePedigreeA(self, previousID, newID):
        self.addOrRemovePeople(isA=True)
    
    def notifyChangePedigreeB(self, previousID, newID):
        self.addOrRemovePeople(isA=False)
    
    def addOrRemovePeople(self, isA):
        previousSet = set(self.nodes.keys())
        newSet = self.appState.aSet.union(self.appState.bSet)
        
        peopleToKill = previousSet.difference(newSet)
        peopleToAdd = newSet.difference(previousSet)
        
        for p in peopleToKill:
            if self.nodes.has_key(p):
                self.nodes[p].kill()
        
        for p in peopleToAdd:
            if self.nodes.has_key(p):
                self.nodes[p].revive()
            else:
                if isA:
                    startingX = 0
                else:
                    startingX = self.right
                startingY = 0
                
                n = node(p,self, startingX, startingY)
                n.allParents,n.allSpouses,n.allChildren = self.appState.ped.countNuclear(p)
                self.nodes[p] = n
                self.scene.addItem(n)
        
        self.refreshGenerations()
        self.refreshHiddenCounts()
    
    def refreshGenerations(self):
        # Keep everyone in the same order that hasn't been killed or moved; don't worry about the ghost nodes
        oldPeople = set()
        movedFromA = set()
        movedFromIntersection = set()
        movedFromB = set()
        newGenerations = {}
        for g in self.generationOrder:
            a,i,b = self.generations[g]
            self.newGenerations[g] = ([],[],[])
            for p in a:
                if not isinstance(p,ghostNode) and not self.nodes[p].killed:
                    if p in self.appState.aSet:
                        oldPeople.add(p)
                        newGenerations[g][0].append(p)
                    else:
                        movedFromA.add(p)
            for p in i:
                if not isinstance(p,ghostNode) and not self.nodes[p].killed:
                    if p in self.appState.abIntersection:
                        oldPeople.add(p)
                        newGenerations[g][1].append(p)
                    else:
                        movedFromIntersection.add(p)
            for p in b:
                if not isinstance(p,ghostNode) and not self.nodes[p].killed:
                    if p in self.appState.bSet:
                        oldPeople.add(p)
                        newGenerations[g][2].append(p)
                    else:
                        movedFromB.add(p)
        self.generations = newGenerations
        
        # Now add everyone that is new, as well as people that were moved to new areas
        for p in self.nodes.iterkeys():
            if p in oldPeople:
                continue
            g = self.appState.ped.getAttribute(p,'generation')
            if not self.generations.has_key(g):
                self.generations[g] = ([],[],[])
            if p in self.appState.aSet:
                if p in movedFromIntersection or p in movedFromB:
                    self.generations[g][0].append(p)    # moved people should start on the right
                else:
                    self.generations[g][0].insert(0,p)  # new people should start on the left
            elif p in self.appState.abIntersection:
                if p in movedFromA:
                    self.generations[g][1].insert(0,p)  # moved people from A should start on the left
                elif p in movedFromB:
                    self.generations[g][1].append(0)    # moved people from B should start on the right
                else:
                    self.generations[g][1].insert(len(self.generations[g][1])/2,p)  # don't think this is actually possible, but new people should start in the middle
            elif p in self.appState.bSet:
                if p in movedFromIntersection or p in movedFromA:
                    self.generations[g][2].insert(0,p)  # moved people shoudl start on the left
                else:
                    self.generations[g][2].append(p)    # new people should start on the right
        
        # Now we need to know which generations actually have people in them
        minGen = None
        maxGen = None
        numGenerations = 0
        emptyGenerations = set()
        for g in self.generationOrder:
            if len(self.generations[g][0]) > 0 or len(self.generations[g][1]) > 0 or len(self.generations[g][2]) > 0:
                numGenerations += 1
                if minGen == None:
                    minGen = g
                else:
                    minGen = min(minGen,g)
                if maxGen == None:
                    maxGen = g
                else:
                    maxGen = max(maxGen,g)
            else:
                emptyGenerations.add(g)
        
        if numGenerations == 0:
            # at this point we know for sure there is no data currently displayed
            return
        
        # Now add ghost nodes where they're needed
        for y,g in enumerate(self.generationOrder):
            if g < minGen or g > maxGen or g in emptyGenerations:
                continue
            for x,p in enumerate(self.generations[g]):
                # Insert ghosts at roughly the same horizontal position (x) where they're needed
                for p2,linkType in self.appState.ped.iterNuclear(p):
                    generationsThatNeedGhosts = []
                    if linkType == self.appState.ped.CHILD_TO_PARENT:
                        genIterator = reversed(self.generationOrder[:y])
                    elif linkType == self.appState.ped.PARENT_TO_CHILD:
                        genIterator = self.generationOrder[y:]
                    else:
                        # For spouses, if they're in the same generation, we already know we don't need any ghosts.
                        if p2 in self.generations[g]:
                            continue
                        # First try down. Later we'll try up
                        genIterator = self.generationOrder[y:]
                    
                    foundTarget = False
                    for g2 in genIterator:
                        if p2 in self.generations[g2]:
                            foundTarget = True
                            break
                        else:
                            if g2 >= minGen and g2 <= maxGen and not g in emptyGenerations:
                                generationsThatNeedGhosts.append(g2)
                    if foundTarget:
                        lastGhost = p
                        for g2 in generationsThatNeedGhosts:
                            if linkType == self.appState.ped.CHILD_TO_PARENT:
                                ghost = ghostNode(g2,lastGhost)
                            else:   # parent to child and our first spouse iteration go down
                                ghost = ghostNode(lastGhost,g2)
                            self.generations[g2].insert(x,ghost)
                            lastGhost = ghost
                        if linkType == self.appState.ped.CHILD_TO_PARENT:
                            lastGhost.parent = p2
                        else:
                            lastGhost.child = p2
                    elif linkType == self.appState.ped.HUSBAND_TO_WIFE or linkType == self.appState.ped.WIFE_TO_HUSBAND:
                        # we have to try again in the other direction for a spouse
                        generationsThatNeedGhosts = []
                        foundTarget = False
                        for g2 in reversed(self.generationOrder[:y]):
                            if p2 in self.generations[g2]:
                                foundTarget = True
                                break
                            else:
                                if g2 >= minGen and g2 <= maxGen and not g in emptyGenerations:
                                    generationsThatNeedGhosts.append(g2)
                        if foundTarget:
                            lastGhost = p
                            for g2 in generationsThatNeedGhosts:
                                ghost = ghostNode(g2,lastGhost)
                                self.generations[g2].insert(x,ghost)
                                lastGhost = ghost
                            lastGhost.parent = p2
        
        # Now update screen targets; sfirst we need to know the widest generation in each section
        aWidth = 0
        iWidth = 0
        bWidth = 0
        numNonEmpty = 0
        for g,(a,i,b) in self.generations.iteritems():
            aWidth = max(len(a),aWidth)
            iWidth = max(len(i),iWidth)
            bWidth = max(len(b),bWidth)
        if aWidth > 0:
            numNonEmpty += 1
        if iWidth > 0:
            numNonEmpty += 1
        if bWidth > 0:
            numNonEmpty += 1
        
        xincrement = (self.right-node.OUTER_RADIUS*2)/max(aWidth+iWidth+bWidth+1,2)   # the extra width is for the slices
        yincrement = (self.bottom-node.OUTER_RADIUS*2)/max(numGenerations-1,2)    # this prevents division by zero, and a two-generation pedigree spread across the top and bottom looks funny
        
        # set the slice target positions
        self.aSlice.targetX = aWidth*xincrement
        self.bSlice.targetX = (aWidth+1+iWidth)*xincrement
        if numNonEmpty > 1:
            self.aSlice.show()
            self.bSlice.show()
        else:
            self.aSlice.hide()
            self.bSlice.show()
        
        # set the node target positions
        y = node.OUTER_RADIUS   # start with an offset; nodes are drawn from the center
        for g in self.generationOrder:
            if g < minGen or g > maxGen or g in emptyGenerations:
                continue
            a,i,b = self.generations[g]
            
            # align a to the left
            x = node.OUTER_RADIUS
            for p in a:
                if not isinstance(p,ghostNode):
                    i = self.nodes[p]
                    i.targetX = x
                    i.targetY = y
                x += xincrement
            
            # TODO: align i to the center
            x = node.OUTER_RADIUS + (aWidth+1)*xincrement
            for p in i:
                if not isinstance(p,ghostNode):
                    i = self.nodes[p]
                    i.targetX = x
                    i.targetY = y
                x += xincrement
            
            # TODO: align b to the right
            x = node.OUTER_RADIUS + (aWidth+1+iWidth+1)*xincrement
            for p in b:
                if not isinstance(p,ghostNode):
                    i = self.nodes[p]
                    i.targetX = x
                    i.targetY = y
                x += xincrement
            
            y += yincrement
    
    def refreshHiddenCounts(self):
        for a in self.nodes.iterkeys():
            self.nodes[a].hiddenParents = 0
            self.nodes[a].hiddenChildren = 0
            self.nodes[a].hiddenSpouses = 0
            for b,l in self.appState.ped.iterNuclear(a):
                if self.nodes.has_key(b) and not self.nodes[b].killed:
                    continue
                elif l == self.appState.ped.PARENT_TO_CHILD:
                    self.nodes[a].hiddenChildren += 1
                elif l == self.appState.ped.CHILD_TO_PARENT:
                    self.nodes[a].hiddenParents += 1
                else:
                    self.nodes[a].hiddenSpouses += 1
    
    def iterLivingNeighbors(self, person, strict=False):
        if not self.nodes.has_key(person) or self.nodes[person].dead or (strict and self.nodes[person].killed):
            raise StopIteration
        else:
            for b,l in self.appState.ped.iterNuclear(person):  # @UnusedVariable
                if not self.nodes.has_key(b) or self.nodes[b].dead or (strict and self.nodes[b].killed):
                    continue
                yield b
    
    def updateValues(self):
        self.aSlice.updateValues()
        self.bSlice.updateValues()
        
        idsToDel = set()
        for p,i in self.nodes.iteritems():
            if i.dead:
                idsToDel.add(p)
                self.corpses.add(i)
                self.scene.removeItem(i)
            else:
                i.updateValues()
        
        # Do some cleaning
        for p in idsToDel:
            del self.nodes[p]
        
        # TODO: do some dot iterations
        
        self.scene.update()