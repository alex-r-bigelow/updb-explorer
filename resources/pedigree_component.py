import random, math, pygraphviz
from PySide.QtGui import QGraphicsScene, QGraphicsItem, QPen, QBrush, QFont, QPainterPath
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
    
    def forceDead(self):
        self.hiding = False
        self.killed = True
        self.dead = True
        self.fadingIn = False
        self.fadingOut = False
        self.opacity = 0.0
    
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
    CLUSTER_FORCE = 0.03
    CLUSTER_SCALE = 0.35
    REPULSION_FORCE = 0.01
    MAX_ENERGY = 1.0
    ENERGY_DECAY = 0.0001
    ENERGY_SWAP_THRESHOLD = 0.1
    CLUSTER_ENERGY = 0.5
    
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
        self.setPos(startingX,startingY)
        self.setZValue(2)
        
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
        if self.panel.getClusterCenter(self.personID) == None:
            self.panel.appState.changeHighlightedNode(self.personID)
    
    def hoverLeaveEvent(self, event):
        if self.panel.getClusterCenter(self.personID) == None:
            self.panel.appState.changeHighlightedNode(None)
    
    def mouseDoubleClickEvent(self, event):
        if self.panel.getClusterCenter(self.personID) == None:
            self.panel.appState.showSecondRoot(self.personID)
    
    def mousePressEvent(self, event):
        if self.panel.getClusterCenter(self.personID) == None:
            self.grabMouse()
            self.ignoreForces = True
        else:
            self.ungrabMouse()
    
    def mouseMoveEvent(self, event):
        if self.panel.getClusterCenter(self.personID) == None:
            self.setPos(event.scenePos())
            # As moving a node will cause disruption, allow me (and consequently my neighbors) to move faster
            self.energy = node.MAX_ENERGY
        else:
            self.ungrabMouse()
    
    def mouseReleaseEvent(self, event):
        self.ungrabMouse()
        if self.panel.getClusterCenter(self.personID) == None:
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
        mx = self.x()
        my = self.y()
        
        dx0 = self.dx
        dy0 = self.dy
        
        # If we're supposed to be clustering, move to the cluster
        clusterCenter = self.panel.getClusterCenter(self.personID)
        if clusterCenter != None:
            xGap = clusterCenter[0]-mx
            yGap = clusterCenter[1]-my
            self.dx += node.CLUSTER_FORCE*xGap
            self.dy += node.CLUSTER_FORCE*yGap
        else:
            if self.ignoreForces:
                return
            
            # Vertical spring toward target
            self.dy = (self.verticalTarget-self.y())*node.GENERATION_FORCE
            
            # Pull from edges
            for e in connectedEdges:
                self.dx += self.horizontalPullFrom(e)
                self.dy += self.verticalPullFrom(e)
            
            # Push from the closest neighbors in the same generation
            for p in generation:
                ox = self.panel.nodes[p].x()
                if ox < mx:
                    leftBound = max(ox,leftBound)
                elif ox > mx:
                    rightBound = min(ox,rightBound)
            if rightBound-mx <= node.FAN_SIZE or mx-leftBound <= node.FAN_SIZE:
                # Shoot, we're overlapping with someone else... is our energy still high?
                if self.energy > node.ENERGY_SWAP_THRESHOLD:
                    # Accelerate away
                    if rightBound-mx > mx-leftBound:
                        distance = max(node.FAN_SIZE,mx-leftBound)
                    else:
                        distance = -max(node.FAN_SIZE,rightBound-mx)
                else:
                    # Otherwise, try swapping places and boosting our energy a little
                    if rightBound-mx > mx-leftBound:
                        distance = -max(node.FAN_SIZE,rightBound-mx)
                    else:
                        distance = max(node.FAN_SIZE,mx-leftBound)
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

class clusterTarget(fadeableGraphicsItem):
    RADIUS = 75
    MAX_OPACITY = 0.9
    FONT = QFont("Monospace", pointSize=16, weight=QFont.Bold)
    FONT.setStyleHint(QFont.TypeWriter)
    
    FIRST_ROOT = 0
    INTERSECTION = 1
    SECOND_ROOT = 2
    NO_ROOT = 3
    
    def __init__(self, panel, x, y, clusterType):
        QGraphicsItem.__init__(self)
        self.panel = panel
        self.clusterType = clusterType
        self.setPos(x,y)
        self.setZValue(3)
    
    def boundingRect(self):
        return QRectF(-clusterTarget.RADIUS,-clusterTarget.RADIUS,clusterTarget.RADIUS*2,clusterTarget.RADIUS*2)
    
    def paint(self, painter, option, widget=None):
        painter.setOpacity(self.opacity*clusterTarget.MAX_OPACITY)
        brush = QBrush(self.panel.appState.BACKGROUND_COLOR)
        pen = QPen(self.panel.appState.MISSING_COLOR, 2.0)
        painter.setPen(pen)
        path = QPainterPath()
        path.addEllipse(-clusterTarget.RADIUS,-clusterTarget.RADIUS,clusterTarget.RADIUS*2,clusterTarget.RADIUS*2)
        painter.fillPath(path,brush)
        painter.drawPath(path)
        
        painter.setFont(clusterTarget.FONT)
        painter.setOpacity(self.opacity)
        if self.clusterType == clusterTarget.FIRST_ROOT:
            painter.setPen(self.panel.appState.ROOT_COLOR)
            self.drawString(painter, "B    ")
            painter.setPen(self.panel.appState.MISSING_COLOR)
            self.drawString(painter, "  -  ")
            painter.setPen(self.panel.appState.SECOND_ROOT_COLOR)
            self.drawString(painter, "    A")
        elif self.clusterType == clusterTarget.INTERSECTION:
            painter.setPen(self.panel.appState.SECOND_ROOT_COLOR)
            self.drawString(painter, "A    ")
            painter.setPen(self.panel.appState.MISSING_COLOR)
            self.drawString(painter, "  " + unichr(8745) + "  ")
            painter.setPen(self.panel.appState.ROOT_COLOR)
            self.drawString(painter, "    B")
        elif self.clusterType == clusterTarget.SECOND_ROOT:
            painter.setPen(self.panel.appState.SECOND_ROOT_COLOR)
            self.drawString(painter, "A    ")
            painter.setPen(self.panel.appState.MISSING_COLOR)
            self.drawString(painter, "  -  ")
            painter.setPen(self.panel.appState.ROOT_COLOR)
            self.drawString(painter, "    B")
        else:
            painter.setPen(self.panel.appState.MISSING_COLOR)
            self.drawString(painter, "U - (  +  )")
            painter.setPen(self.panel.appState.SECOND_ROOT_COLOR)
            self.drawString(painter, "     A     ")
            painter.setPen(self.panel.appState.ROOT_COLOR)
            self.drawString(painter, "         B ")
    
    def drawString(self, painter, s):
        # QPainter.drawStaticText isn't supported in pyside, so this is an ugly workaround
        painter.drawText(-clusterTarget.RADIUS,-clusterTarget.RADIUS,clusterTarget.RADIUS*2,clusterTarget.RADIUS*2,
                         Qt.AlignVCenter | Qt.AlignHCenter, s)
        
    def mouseDoubleClickEvent(self, event):
        if not self.killed and event.button() == Qt.LeftButton:
            if self.clusterType == clusterTarget.FIRST_ROOT:
                self.panel.appState.showSecondRoot(None)
            elif self.clusterType == clusterTarget.SECOND_ROOT:
                self.panel.appState.setRoot(self.panel.appState.secondRoot)
            elif self.clusterType == clusterTarget.INTERSECTION:
                result = self.panel.centerCluster
                self.panel.appState.showSecondRoot(None)
                self.panel.appState.setRoot(None)
                self.panel.appState.tweakVisibleSet(result)
            else:
                result = self.panel.noCluster
                self.panel.appState.showSecondRoot(None)
                self.panel.appState.setRoot(None)
                self.panel.appState.tweakVisibleSet(result)

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
        self.minGen = None
        self.maxGen = None
        
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        # TODO: figure out these sizes differently...
        self.bottom = 400
        self.right = 1900
        
        self.clusterTargets = {}
        self.leftCluster = set()
        self.leftClusterX = self.right / 5
        self.leftClusterY = self.bottom / 2
        self.leftTarget = clusterTarget(self,self.leftClusterX,self.leftClusterY,clusterTarget.SECOND_ROOT)
        self.scene.addItem(self.leftTarget)
        self.leftTarget.forceDead()
        
        self.centerCluster = set()
        self.centerClusterX = self.right / 2
        self.centerClusterY = 3*self.bottom / 4
        self.centerTarget = clusterTarget(self,self.centerClusterX,self.centerClusterY,clusterTarget.INTERSECTION)
        self.scene.addItem(self.centerTarget)
        self.centerTarget.forceDead()
        
        self.rightCluster = set()
        self.rightClusterX = 4*self.right / 5
        self.rightClusterY = self.bottom / 2
        self.rightTarget = clusterTarget(self,self.rightClusterX,self.rightClusterY,clusterTarget.FIRST_ROOT)
        self.scene.addItem(self.rightTarget)
        self.rightTarget.forceDead()
        
        self.noCluster = set()
        self.noClusterX = self.right / 2
        self.noClusterY = self.bottom / 4
        self.noTarget = clusterTarget(self,self.noClusterX,self.noClusterY,clusterTarget.NO_ROOT)
        self.scene.addItem(self.noTarget)
        self.noTarget.forceDead()
        
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
        #self.initialLayout(list(peopleToAdd))
        self.refreshHiddenCounts()
    
    def refreshGenerations(self):
        self.generations = {}
        self.minGen = 0
        self.maxGen = 0
        
        for p,i in self.nodes.iteritems():
            if i.killed:
                continue
            gen = self.appState.ped.getAttribute(p,'generation')
            self.minGen = min(self.minGen,gen)
            self.maxGen = max(self.maxGen,gen)
            
            if not self.generations.has_key(gen):
                self.generations[gen] = set()
            self.generations[gen].add(p)
        
        offset = node.FAN_SIZE*0.5 # center-based drawing
        increment = (self.bottom-node.FAN_SIZE) / (max(self.maxGen-self.minGen-1,2))
        
        for p,i in self.nodes.iteritems():
            if not i.dead:
                slot = self.maxGen - self.appState.ped.getAttribute(p,'generation')
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
    
    def getClusterCenter(self, person):
        return self.clusterTargets.get(person,None)
    
    def notifySetRoot(self, previous, prevSet, new, newSet):
        self.leftTarget.kill()
        self.centerTarget.kill()
        self.rightTarget.kill()
        self.noTarget.kill()
        
        self.clusterTargets = {}
        
        for i in self.nodes.itervalues():
            i.energy = node.MAX_ENERGY
    
    def notifyShowSecondRoot(self, previous, prevSet, new, newSet):
        if new == None:
            self.notifySetRoot(previous, prevSet, new, newSet)
            return
        fullSecondRootSet = set(self.appState.ped.iterDown(new))
        self.leftCluster = newSet
        self.centerCluster = self.appState.rootSet.intersection(fullSecondRootSet)
        self.rightCluster = self.appState.rootSet.difference(fullSecondRootSet)
        self.noCluster = set()
        
        leftCenterOfMassX = 0
        leftCenterOfMassY = 0
        
        centerCenterOfMassX = 0
        centerCenterOfMassY = 0
        
        rightCenterOfMassX = 0
        rightCenterOfMassY = 0
        
        noCenterOfMassX = 0
        noCenterOfMassY = 0
        
        for n,i in self.nodes.iteritems():
            if n in self.leftCluster:
                leftCenterOfMassX += i.x()
                leftCenterOfMassY += i.y()
            elif n in self.centerCluster:
                centerCenterOfMassX += i.x()
                centerCenterOfMassY += i.y()
            elif n in self.rightCluster:
                rightCenterOfMassX += i.x()
                rightCenterOfMassY += i.y()
            else:
                noCenterOfMassX += i.x()
                noCenterOfMassY += i.y()
                self.noCluster.add(n)
                
        if len(self.leftCluster) > 0:
            leftCenterOfMassX /= len(self.leftCluster)
            leftCenterOfMassY /= len(self.leftCluster)
        if len(self.centerCluster) > 0:
            centerCenterOfMassX /= len(self.centerCluster)
            centerCenterOfMassY /= len(self.centerCluster)
        if len(self.rightCluster) > 0:
            rightCenterOfMassX /= len(self.rightCluster)
            rightCenterOfMassY /= len(self.rightCluster)
        if len(self.noCluster) > 0:
            noCenterOfMassX /= len(self.noCluster)
            noCenterOfMassY /= len(self.noCluster)
        
        self.clusterTargets = {}
        for n,i in self.nodes.iteritems():
            i.energy = node.CLUSTER_ENERGY
            if n in self.leftCluster:
                targetX = node.CLUSTER_SCALE*(i.x()-leftCenterOfMassX)+self.leftClusterX
                targetY = node.CLUSTER_SCALE*(i.y()-leftCenterOfMassY)+self.leftClusterY
                self.clusterTargets[n] = (targetX,targetY)
            elif n in self.centerCluster:
                targetX = node.CLUSTER_SCALE*(i.x()-centerCenterOfMassX)+self.centerClusterX
                targetY = node.CLUSTER_SCALE*(i.y()-centerCenterOfMassY)+self.centerClusterY
                self.clusterTargets[n] = (targetX,targetY)
            elif n in self.rightCluster:
                targetX = node.CLUSTER_SCALE*(i.x()-rightCenterOfMassX)+self.rightClusterX
                targetY = node.CLUSTER_SCALE*(i.y()-rightCenterOfMassY)+self.rightClusterY
                self.clusterTargets[n] = (targetX,targetY)
            else:
                assert n in self.noCluster
                targetX = node.CLUSTER_SCALE*(i.x()-noCenterOfMassX)+self.noClusterX
                targetY = node.CLUSTER_SCALE*(i.y()-noCenterOfMassY)+self.noClusterY
                self.clusterTargets[n] = (targetX,targetY)
        
        self.leftTarget.revive()
        self.centerTarget.revive()
        self.rightTarget.revive()
        self.noTarget.revive()
    
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
    
    def initialLayout(self, limitTo=None):
        if limitTo == None:
            limitTo = list(self.nodes.iterkeys())
        # TODO
    
    def updateValues(self):
        # Update opacity values, positions for this frame
        self.leftTarget.updateValues()
        self.centerTarget.updateValues()
        self.rightTarget.updateValues()
        self.noTarget.updateValues()
        
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
            if not i.dead and not i.killed:
                gen = self.appState.ped.getAttribute(p,'generation')
                generation = self.generations[math.floor(gen)].union(self.generations[math.ceil(gen)])
                i.applyForces(self.iterLivingNeighbors(p, strict=True),generation,0,self.right)
        self.scene.update()