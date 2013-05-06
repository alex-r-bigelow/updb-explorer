import random
from PySide.QtGui import QGraphicsScene, QGraphicsItem, QPen, QBrush, QColor, QPainterPath
from PySide.QtCore import Qt, QRectF, QTimer
from app_state import AppComponent
from pedigree_data import Pedigree

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

class node(fadeableGraphicsItem):
    MALE = 'M'
    FEMALE = 'F'
    
    SIZE = 12
    FAN_SIZE = 36
    STROKE_WEIGHT = 3
    
    HORIZONTAL_FORCE = 0.005
    VERTICAL_FORCE = 0.03
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
        
        if startingX == None:
            startingX = random.randint(0,self.panel.right)
        if startingY == None:
            startingY = random.randint(0,self.panel.bottom)
        self.setX(startingX)
        self.setY(startingY)
        
    def boundingRect(self):
        radius = node.FAN_SIZE*0.5
        return QRectF(-radius,-radius,node.FAN_SIZE,node.FAN_SIZE)
    
    def paint(self, painter, option, widget=None):
        fill,stroke,showFan = self.panel.appState.getColors(self.personID)
        painter.setOpacity(self.opacity)
        painter.setPen(QPen(stroke,node.STROKE_WEIGHT))
        brush = QBrush(fill)
        
        outerRadius = node.FAN_SIZE*0.5
        innerRadius = node.SIZE*0.5
        
        if showFan:
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
            painter.fillPath(path,brush)
            
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
            painter.fillPath(path1,brush)
            painter.fillPath(path2,brush)
            
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
            painter.fillPath(path,brush)
        
        # Center shape
        if self.sex == node.MALE:
            painter.fillRect(-innerRadius,-innerRadius,node.SIZE,node.SIZE,brush)
            painter.drawRect(-innerRadius,-innerRadius,node.SIZE,node.SIZE)
        elif self.sex == node.FEMALE:
            path = QPainterPath()
            path.addEllipse(-innerRadius,-innerRadius,node.SIZE,node.SIZE)
            painter.fillPath(path,brush)
            painter.drawPath(path)
        else:
            raise Exception('Unknown sex.')
    
    def hoverEnterEvent(self, event):
        self.panel.appState.changeHighlightedNode(self.personID)
    
    def hoverLeaveEvent(self, event):
        self.panel.appState.changeHighlightedNode(None)
    
    def mouseDoubleClickEvent(self, event):
        self.panel.appState.showSecondRoot(self.personID)
    
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
                self.panel.expandOrCollapse(self,PedigreeComponent.UP)
            elif y > innerRadius:
                self.panel.expandOrCollapse(self,PedigreeComponent.DOWN)
        elif (x < -innerRadius or x > innerRadius) and y > -innerRadius and y < innerRadius:
            self.panel.expandOrCollapse(self,PedigreeComponent.HORIZONTAL)
        
    def updateValues(self, neighbors):
        # Average every neighbor's energy with my own, then decay it a little
        fadeableGraphicsItem.updateValues(self)
        for n in neighbors:
            self.energy += n.energy
        self.energy = max(0,(self.energy/(len(neighbors)+1)-node.ENERGY_DECAY))
        self.moveBy(self.dx,self.dy)
    
    def horizontalPullFrom(self, n):
        return node.HORIZONTAL_FORCE*(self.panel.nodes[n].x() - self.panel.nodes[self.personID].x())
    
    def verticalPullFrom(self, n):
        l = self.panel.appState.ped.getLink(self.personID,n)
        if l == Pedigree.HUSBAND_TO_WIFE or l == Pedigree.WIFE_TO_HUSBAND:
            return node.VERTICAL_FORCE*(self.panel.nodes[n].y() - self.panel.nodes[self.personID].y())
        else:
            return 0
    
    def applyForces(self, connectedEdges, generation, leftBound, rightBound):
        if self.ignoreForces:
            return
        
        dx0 = self.dx
        dy0 = self.dy
        
        # Vertical spring toward target
        self.dy = (self.verticalTarget-self.y())*node.GENERATION_FORCE
        
        # Pull from edges
        for e in connectedEdges:
            self.dx += self.horizontalPullFrom(e)
            self.dy += self.verticalPullFrom(e)
        
        # Push from the closest neighbors in the same generation
        mx = self.x()
        for p in generation:
            ox = self.panel.nodes[p].x()
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

class edgeLayer(QGraphicsItem):
    def __init__(self, panel):
        QGraphicsItem.__init__(self)
        self.panel = panel
    
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
                    pen = QPen(color, 2, Qt.DotLine)
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
        self.minGen = None
        self.maxGen = None
        
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        # TODO: figure out these sizes differently...
        self.bottom = 300
        self.right = 1900
        
        self.edges = edgeLayer(self)
        self.scene.addItem(self.edges)
        
        self.timer = QTimer(self.view)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(PedigreeComponent.FRAME_DURATION)
    
    def addCorpse(self,i):
        self.corpses.add(i)
    
    def dumpCorpses(self):
        self.corpses = set()
    
    def notifyTweakVisibleSet(self, previous, new):
        peopleToKill = previous.difference(new)
        peopleToAdd = new.difference(previous)
        
        for p in peopleToKill:
            if self.nodes.has_key(p):
                self.nodes[p].kill()
        
        for p in peopleToAdd:
            if self.nodes.has_key(p):
                self.nodes[p].revive()
            else:
                startingX = None
                startingY = None
                # TODO: fly in directions
                '''if direction == PedigreeComponent.UP:
                    startingY = 0
                elif direction == PedigreeComponent.HORIZONTAL:
                    startingX = 0
                elif direction == PedigreeComponent.DOWN:
                    startingY = self.bottom'''
                
                n = node(p,self,self.appState.ped.getAttribute(p,'sex','?'), startingX, startingY)
                n.allParents,n.allSpouses,n.allChildren = self.appState.ped.countNuclear(p)
                self.nodes[p] = n
                self.scene.addItem(n)
        
        self.refreshGenerations()
        self.refreshHiddenCounts()
    
    def refreshGenerations(self):
        self.generations = {}
        self.minGen = None
        self.maxGen = None
        
        for p,i in self.nodes.iteritems():
            if i.killed:
                continue
            gen = self.appState.ped.getAttribute(p,'generation',0)
            
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
        
        offset = node.SIZE*0.5 # center-based drawing
        increment = self.bottom / (max(self.maxGen-self.minGen+1,2))
        
        for p,i in self.nodes.iteritems():
            if not i.dead:
                slot = self.maxGen - self.appState.ped.getAttribute(p,'generation',self.maxGen) - 1
                self.nodes[p].verticalTarget = self.bottom - slot*increment - offset
    
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
    
    def notifyShowSecondRoot(self, previous, new):
        pass
    
    def expandOrCollapse(self, item, direction):
        if item.killed:
            return
        existingSet = self.appState.visibleSet
        if direction == PedigreeComponent.UP:
            if item.allParents == 0:
                return
            elif item.hiddenParents > 0:
                self.appState.tweakVisibleSet(existingSet.union(self.appState.ped.iterParents(item.personID)))
            else:
                # throw away the branch in two steps
                self.appState.tweakVisibleSet(existingSet.difference(self.appState.ped.iterParents(item.personID)))
                self.cleanUp(item.personID)
        elif direction == PedigreeComponent.HORIZONTAL:
            if item.allSpouses == 0:
                return
            elif item.hiddenSpouses > 0:
                self.appState.tweakVisibleSet(existingSet.union(self.appState.ped.iterSpouses(item.personID)))
            else:
                # throw away the branch in two steps
                self.appState.tweakVisibleSet(existingSet.difference(self.appState.ped.iterSpouses(item.personID)))
                self.cleanUp(item.personID)
        elif direction == PedigreeComponent.DOWN:
            if item.allChildren == 0:
                return
            elif item.hiddenChildren > 0:
                self.appState.tweakVisibleSet(existingSet.union(self.appState.ped.iterChildren(item.personID)))
            else:
                # throw away the branch in two steps
                self.appState.tweakVisibleSet(existingSet.difference(self.appState.ped.iterChildren(item.personID)))
                self.cleanUp(item.personID)
    
    def cleanUp(self, person):
        # throw away any connected components that aren't connected to person
        nodesToKeep = set()
        
        # Iterate down then up BFS style
        toVisit = [person]
        while len(toVisit) > 0:
            a = toVisit.pop(0)
            if not a in nodesToKeep:
                nodesToKeep.add(a)
                toVisit.extend(self.iterLivingNeighbors(a, strict=True))
        
        self.appState.tweakVisibleSet(nodesToKeep)
    
    def iterLivingNeighbors(self, person, strict=False):
        if not self.nodes.has_key(person) or self.nodes[person].dead or (strict and self.nodes[person].killed):
            raise StopIteration
        else:
            for b,l in self.appState.ped.iterNuclear(person):  # @UnusedVariable
                if not self.nodes.has_key(b) or self.nodes[b].dead or (strict and self.nodes[b].killed):
                    continue
                yield b
    
    def updateValues(self):
        # Update opacity values, positions for this frame
        idsToDel = set()
        for p,i in self.nodes.iteritems():
            if i.dead:
                idsToDel.add(p)
                self.corpses.add(i)
                self.scene.removeItem(i)
            else:
                i.updateValues([self.nodes[n] for n in self.iterLivingNeighbors(p, strict=True)])
        
        # Do some cleaning
        for p in idsToDel:
            del self.nodes[p]
        
        self.refreshHiddenCounts()
        self.refreshGenerations()
        
        # Finally, prep the next update by applying forces
        for p,i in self.nodes.iteritems():
            i.applyForces(self.iterLivingNeighbors(p, strict=True),self.generations[self.appState.ped.getAttribute(p,'generation',self.maxGen)],0,self.right)
        self.scene.update()
    
    '''
    
    def addPeople(self, people, direction = None):
        # Create the node objects, update the number of generations
        for p in people:
            if self.g.node.has_key(p):
                n = self.g.node[p]['item']
                n.revive()
            else:
                startingX = None
                startingY = None
                if direction == PedigreeComponent.UP:
                    startingY = 0
                elif direction == PedigreeComponent.HORIZONTAL:
                    startingX = 0
                elif direction == PedigreeComponent.DOWN:
                    startingY = self.bottom
                
                n = node(p,self,self.appState.ped.getAttribute(p,'sex','?'), startingX, startingY)
                n.allParents,n.allSpouses,n.allChildren = self.appState.ped.countNuclear(p)
                n.setZValue(1)
                self.g.add_node(p, {'item':n})
                self.scene.addItem(n)
        # Add links to other people that are in the pedigree
        for p in people:
            for p2,t in self.appState.ped.iterNuclear(p):
                if self.g.node.has_key(p2):
                    if self.g.edge[p].has_key(p2):
                        e = self.g.edge[p][p2]['item']
                        e.revive()
                    else:
                        e = None
                        if t == self.appState.ped.CHILD_TO_PARENT or t == self.appState.ped.PARENT_TO_CHILD:
                            e = edge(self.g.node[p]['item'],self.g.node[p2]['item'],edge.GENETIC)
                        else:
                            e = edge(self.g.node[p]['item'],self.g.node[p2]['item'],edge.MARRIAGE)
                        e.setZValue(0)
                        self.g.add_edge(p, p2, {'item':e})
                        self.scene.addItem(e)
        self.refreshHiddenCounts()
        self.refreshGenerations()
        self.dumpCorpses() # painting happens in the same thread addPeople is in... we only want to release dead QGraphicsItems every once in a while
    
    def expandOrCollapse(self, item, direction):
        if item.dead:
            return
        if direction == PedigreeComponent.UP:
            if item.allParents == 0:
                return
            elif item.hiddenParents > 0:
                self.addPeople(set(self.appState.ped.iterParents(item.personID)),PedigreeComponent.UP)
            else:
                self.discardPeople(set(self.appState.ped.iterParents(item.personID)))
                self.cleanUp(item.personID)
        elif direction == PedigreeComponent.HORIZONTAL:
            if item.allSpouses == 0:
                return
            elif item.hiddenSpouses > 0:
                self.addPeople(set(self.appState.ped.iterSpouses(item.personID)),PedigreeComponent.HORIZONTAL)
            else:
                self.discardPeople(set(self.appState.ped.iterSpouses(item.personID)))
                self.cleanUp(item.personID)
        elif direction == PedigreeComponent.DOWN:
            if item.allChildren == 0:
                return
            elif item.hiddenChildren > 0:
                self.addPeople(set(self.appState.ped.iterChildren(item.personID)),PedigreeComponent.DOWN)
            else:
                self.discardPeople(set(self.appState.ped.iterChildren(item.personID)))
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
            for p,t in self.appState.ped.iterNuclear(person):
                if self.g.node.has_key(p) and not self.g.node[p]['item'].killed:
                    continue
                elif t == self.appState.ped.PARENT_TO_CHILD:
                    self.g.node[person]['item'].hiddenChildren += 1
                elif t == self.appState.ped.CHILD_TO_PARENT:
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
            gen = self.appState.ped.getAttribute(p,'generation',0)
            
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
        
        bottom = self.bottom
        offset = node.SIZE*0.5 # center-based drawing
        increment = bottom / (max(self.maxGen-self.minGen+1,2))
        
        for p,attrs in self.g.node.iteritems():
            n = attrs['item']
            if not n.dead:
                slot = self.maxGen - self.appState.ped.getAttribute(p,'generation',self.maxGen) - 1
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
            self.addCorpse(e)  # keep a reference to the item around until we know the main thread won't try to access it anymore (remember, this function is called from a timer)
            self.g.remove_edge(source, target)
            if e in existingItems:
                self.scene.removeItem(e)
        for p in nodesToRemove:
            n = self.g.node[p]['item']
            self.addCorpse(n)  # keep a reference to the item around until we know the main thread won't try to access it anymore (remember, this function is called from a timer)
            self.g.remove_node(p)
            if n in existingItems:
                self.scene.removeItem(n)
        self.refreshHiddenCounts()
        self.refreshGenerations()
        
        # Finally, prep the next update by applying forces
        for p,attrs in self.g.node.iteritems():
            connectedEdges = set(attrs['item'] for attrs in self.g.edge[p].itervalues())
            generationNodes = set(self.g.node[r]['item'] for r in self.generations[self.appState.ped.getAttribute(p,'generation',self.maxGen)])
            attrs['item'].applyForces(connectedEdges,generationNodes,0,self.right)
        self.scene.update()
    '''