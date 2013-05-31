import random, math
from PySide.QtGui import QGraphicsScene, QGraphicsItem, QPen, QPainterPath, QFont
from PySide.QtCore import Qt, QRectF, QTimer
from app_state import AppComponent

class fadeableGraphicsItem(QGraphicsItem):
    OPACITY_SPEED = 0.05
    HIDDEN_OPACITY = 0.0
    SPATIAL_SPEED = 1000.0
    
    def __init__(self, x, y):
        QGraphicsItem.__init__(self)
        self.hiding = False
        self.killed = False
        self.dead = False
        self.frozen = False
        
        self.opacity = 0.0
        self.targetX = x
        self.targetY = y
        self.originX = x
        self.originY = y
        self.vx = 0
        self.vy = 0
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
        if x == self.targetX and y == self.targetY:
            self.originX = x
            self.originY = y
            self.vx = 0
            self.vy = 0
            return
        
        ox = float(x - self.originX)
        oy = float(y - self.originY)
        tx = float(self.targetX - x)
        ty = float(self.targetY - y)
        
        if abs(tx) >= abs(ox):
            dx = tx
        else:
            dx = ox
        
        if abs(ty) >= abs(oy):
            dy = ty
        else:
            dy = oy
        
        angle = math.atan2(dy,dx)
        a = fadeableGraphicsItem.SPATIAL_SPEED/(abs(dx)+abs(dy))
        self.vx += math.cos(angle)*a
        self.vy += math.sin(angle)*a
        
        if abs(self.vx) >= abs(tx) - 1.0:
            self.vx = tx
        if abs(self.vy) >= abs(ty) - 1.0:
            self.vy = ty
        
        self.setPos(x+self.vx,y+self.vy)
    
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
    STROKE_WEIGHT = 6
    
    EXPANDED_RADIUS = 18
    EXPANDED_RECT = QRectF(-EXPANDED_RADIUS,-EXPANDED_RADIUS,
                          EXPANDED_RADIUS*2,EXPANDED_RADIUS*2)
    EXPANDED_CIRCLE = QPainterPath()
    EXPANDED_CIRCLE.addEllipse(EXPANDED_RECT)
    
    COLLAPSED_RADIUS = 6
    COLLAPSED_RECT = QRectF(-COLLAPSED_RADIUS,-COLLAPSED_RADIUS,
                           COLLAPSED_RADIUS*2,COLLAPSED_RADIUS*2)
    COLLAPSED_CIRCLE = QPainterPath()
    COLLAPSED_CIRCLE.addEllipse(COLLAPSED_RECT)
    
    FAN_OPACITY = 0.75
    FAN_WEIGHT = 1.5
    FAN_GAP = 2
    FAN_RADIUS = 3
    
    TOP_RECT = QRectF(-FAN_RADIUS,-EXPANDED_RADIUS+FAN_GAP,
                     FAN_RADIUS*2,FAN_RADIUS*2)
    
    TOP_TRIANGLE = QPainterPath()
    TOP_TRIANGLE.moveTo(-FAN_RADIUS,-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2)
    TOP_TRIANGLE.lineTo(0,-EXPANDED_RADIUS+FAN_GAP)
    TOP_TRIANGLE.lineTo(FAN_RADIUS,-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2)
    TOP_TRIANGLE.lineTo(-FAN_RADIUS,-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2)
    
    TOP_TRIANGLE_HALF = QPainterPath()
    TOP_TRIANGLE_HALF.moveTo(0,-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2)
    TOP_TRIANGLE_HALF.lineTo(0,-EXPANDED_RADIUS+FAN_GAP)
    TOP_TRIANGLE_HALF.lineTo(FAN_RADIUS,-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2)
    TOP_TRIANGLE_HALF.lineTo(0,-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2)
    
    LEFT_RECT = QRectF(-EXPANDED_RADIUS+FAN_GAP,-FAN_RADIUS,
                      FAN_RADIUS*2,FAN_RADIUS*2)
    
    LEFT_TRIANGLE = QPainterPath()
    LEFT_TRIANGLE.moveTo(-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2,-FAN_RADIUS)
    LEFT_TRIANGLE.lineTo(-EXPANDED_RADIUS+FAN_GAP,0)
    LEFT_TRIANGLE.lineTo(-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2,FAN_RADIUS)
    LEFT_TRIANGLE.lineTo(-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2,-FAN_RADIUS)
    
    LEFT_TRIANGLE_HALF = QPainterPath()
    LEFT_TRIANGLE_HALF.moveTo(-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2,0)
    LEFT_TRIANGLE_HALF.lineTo(-EXPANDED_RADIUS+FAN_GAP,0)
    LEFT_TRIANGLE_HALF.lineTo(-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2,-FAN_RADIUS)
    LEFT_TRIANGLE_HALF.lineTo(-EXPANDED_RADIUS+FAN_GAP+FAN_RADIUS*2,0)
    
    RIGHT_RECT = QRectF(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,-FAN_RADIUS,
                       FAN_RADIUS*2,FAN_RADIUS*2)
    
    RIGHT_TRIANGLE = QPainterPath()
    RIGHT_TRIANGLE.moveTo(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,-FAN_RADIUS)
    RIGHT_TRIANGLE.lineTo(EXPANDED_RADIUS-FAN_GAP,0)
    RIGHT_TRIANGLE.lineTo(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,FAN_RADIUS)
    RIGHT_TRIANGLE.lineTo(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,-FAN_RADIUS)
    
    RIGHT_TRIANGLE_HALF = QPainterPath()
    RIGHT_TRIANGLE_HALF.moveTo(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,0)
    RIGHT_TRIANGLE_HALF.lineTo(EXPANDED_RADIUS-FAN_GAP,0)
    RIGHT_TRIANGLE_HALF.lineTo(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,FAN_RADIUS)
    RIGHT_TRIANGLE_HALF.lineTo(EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,0)
    
    BOTTOM_RECT = QRectF(-FAN_RADIUS,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2,
                        FAN_RADIUS*2,FAN_RADIUS*2)
    
    BOTTOM_TRIANGLE = QPainterPath()
    BOTTOM_TRIANGLE.moveTo(-FAN_RADIUS,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2)
    BOTTOM_TRIANGLE.lineTo(0,EXPANDED_RADIUS-FAN_GAP)
    BOTTOM_TRIANGLE.lineTo(FAN_RADIUS,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2)
    BOTTOM_TRIANGLE.lineTo(-FAN_RADIUS,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2)
    
    BOTTOM_TRIANGLE_HALF = QPainterPath()
    BOTTOM_TRIANGLE_HALF.moveTo(0,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2)
    BOTTOM_TRIANGLE_HALF.lineTo(0,EXPANDED_RADIUS-FAN_GAP)
    BOTTOM_TRIANGLE_HALF.lineTo(-FAN_RADIUS,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2)
    BOTTOM_TRIANGLE_HALF.lineTo(0,EXPANDED_RADIUS-FAN_GAP-FAN_RADIUS*2)
    
    SCISSOR_OPACITY = 1.0
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
        self.hoverPos = None
        self.highlightedExternally = False
        
        self.setZValue(3)
    
    def boundingRect(self):
        if self.hoverPos != None or self.highlightedExternally:
            radius = node.EXPANDED_RADIUS + node.STROKE_WEIGHT
        else:
            radius = node.COLLAPSED_RADIUS + node.STROKE_WEIGHT
        return QRectF(-radius,-radius,radius*2,radius*2)
    
    def drawScissors(self, painter):
        if self.hoverPos == None:
            return
        painter.setOpacity(node.SCISSOR_OPACITY)
        painter.setPen(QPen(self.panel.appState.BACKGROUND_COLOR,node.SCISSOR_WEIGHT))
        
        if node.TOP_RECT.contains(self.hoverPos):
            if self.allParents-self.hiddenParents > 0:
                painter.drawLine(node.TOP_RECT.topLeft(),node.TOP_RECT.bottomRight())
                painter.drawLine(node.TOP_RECT.bottomLeft(),node.TOP_RECT.topRight())
            elif self.hiddenParents > 0:
                painter.drawPath(node.TOP_TRIANGLE)
                painter.fillPath(node.TOP_TRIANGLE,self.panel.appState.BACKGROUND_COLOR)
        elif (node.LEFT_RECT.contains(self.hoverPos) \
              or node.RIGHT_RECT.contains(self.hoverPos)):
            if self.allSpouses-self.hiddenSpouses > 0:
                painter.drawLine(node.LEFT_RECT.topLeft(),node.LEFT_RECT.bottomRight())
                painter.drawLine(node.LEFT_RECT.bottomLeft(),node.LEFT_RECT.topRight())
                painter.drawLine(node.RIGHT_RECT.topLeft(),node.RIGHT_RECT.bottomRight())
                painter.drawLine(node.RIGHT_RECT.bottomLeft(),node.RIGHT_RECT.topRight())
            elif self.hiddenSpouses > 0:
                painter.drawPath(node.LEFT_TRIANGLE)
                painter.fillPath(node.LEFT_TRIANGLE,self.panel.appState.BACKGROUND_COLOR)
                painter.drawPath(node.RIGHT_TRIANGLE)
                painter.fillPath(node.RIGHT_TRIANGLE,self.panel.appState.BACKGROUND_COLOR)
        elif node.BOTTOM_RECT.contains(self.hoverPos):
            if self.allChildren-self.hiddenChildren > 0:
                painter.drawLine(node.BOTTOM_RECT.topLeft(),node.BOTTOM_RECT.bottomRight())
                painter.drawLine(node.BOTTOM_RECT.bottomLeft(),node.BOTTOM_RECT.topRight())
            elif self.hiddenChildren > 0:
                painter.drawPath(node.BOTTOM_TRIANGLE)
                painter.fillPath(node.BOTTOM_TRIANGLE,self.panel.appState.BACKGROUND_COLOR)
    
    def drawFan(self, painter):
        painter.setOpacity(self.opacity*node.FAN_OPACITY)
        painter.setPen(QPen(self.panel.appState.BACKGROUND_COLOR,node.FAN_WEIGHT))
        fill = self.panel.appState.BACKGROUND_COLOR
        
        # Parents
        if self.allParents > 0:
            painter.drawPath(node.TOP_TRIANGLE)
            if self.hiddenParents == 0:
                painter.fillPath(node.TOP_TRIANGLE,fill)
            elif self.hiddenParents < self.allParents:
                painter.fillPath(node.TOP_TRIANGLE_HALF,fill)
        
        # Spouses
        if self.allSpouses > 0:
            painter.drawPath(node.LEFT_TRIANGLE)
            painter.drawPath(node.RIGHT_TRIANGLE)
            if self.hiddenSpouses == 0:
                painter.fillPath(node.LEFT_TRIANGLE,fill)
                painter.fillPath(node.RIGHT_TRIANGLE,fill)
            elif self.hiddenSpouses < self.allSpouses:
                painter.fillPath(node.LEFT_TRIANGLE_HALF,fill)
                painter.fillPath(node.RIGHT_TRIANGLE_HALF,fill)
        
        # Children
        if self.allChildren > 0:
            painter.drawPath(node.BOTTOM_TRIANGLE)
            if self.hiddenChildren == 0:
                painter.fillPath(node.BOTTOM_TRIANGLE,fill)
            elif self.hiddenChildren < self.allChildren:
                painter.fillPath(node.BOTTOM_TRIANGLE_HALF,fill)
    
    def paint(self, painter, option, widget=None):
        painter.setOpacity(self.opacity)
        sex = self.panel.appState.ped.getAttribute(self.personID,'sex','?')
        fill,stroke = self.panel.appState.getColors(self.personID)
        if stroke != None:
            stroke = QPen(stroke,node.STROKE_WEIGHT)
            painter.setPen(stroke)
        
        if self.hoverPos != None or self.highlightedExternally:
            # Center shape
            if sex == 'M':
                if stroke != None:
                    painter.drawRect(node.EXPANDED_RECT)
                painter.fillRect(node.EXPANDED_RECT,fill)
            elif sex == 'F':
                if stroke != None:
                    painter.drawPath(node.EXPANDED_CIRCLE)
                painter.fillPath(node.EXPANDED_CIRCLE,fill)
            else:
                raise Exception('Unknown sex.')
            
            self.drawFan(painter)
            self.drawScissors(painter)
        else:
            if sex == 'M':
                if stroke != None:
                    painter.drawRect(node.COLLAPSED_RECT)
                painter.fillRect(node.COLLAPSED_RECT,fill)
            elif sex == 'F':
                if stroke != None:
                    painter.drawPath(node.COLLAPSED_CIRCLE)
                painter.fillPath(node.COLLAPSED_CIRCLE,fill)
            else:
                raise Exception('Unknown sex.')
    
    def hoverEnterEvent(self, event):
        self.panel.appState.highlightAnIndividual(self.personID)
        self.hoverPos = event.pos()
        self.prepareGeometryChange()
    
    def hoverLeaveEvent(self, event):
        self.panel.appState.highlightAnIndividual(None)
        self.hoverPos = None
        self.prepareGeometryChange()
    
    def hoverMoveEvent(self, event):
        self.hoverPos = event.pos()
    
    def mouseDoubleClickEvent(self, event):
        self.panel.appState.showIndividualDetails(self.personID)
    
    def mousePressEvent(self, event):
        self.grabMouse()
        self.freeze()
        if event.button() == Qt.LeftButton:
            p = event.pos()
            if node.TOP_RECT.contains(p):
                self.snipDirection = node.UP
            elif node.LEFT_RECT.contains(p) or node.RIGHT_RECT.contains(p):
                self.snipDirection = node.HORIZONTAL
            elif node.BOTTOM_RECT.contains(p):
                self.snipDirection = node.DOWN
            else:
                self.snipDirection = None
    
    def mouseMoveEvent(self, event):
        if self.snipDirection == None:
            self.setPos(event.scenePos())
    
    def mouseReleaseEvent(self, event):
        self.ungrabMouse()
        self.thaw()
        
        if event.button() == Qt.RightButton:
            self.panel.appState.showIndividualContextMenu(self.personID)
        elif event.button() == Qt.LeftButton:
            if self.snipDirection != None:
                # Only perform a snip action if we started and ended in the same area
                p = event.pos()
                
                if node.TOP_RECT.contains(p) and self.snipDirection == node.UP:
                    
                    if self.allParents - self.hiddenParents > 0:
                        self.panel.appState.snip(self.personID,
                                                 [self.panel.appState.ped.CHILD_TO_PARENT])
                    elif self.allParents > 0:
                        self.panel.appState.expand(self.personID,
                                   set(self.panel.appState.ped.iterParents(self.personID)))
                
                elif (node.LEFT_RECT.contains(p) or node.RIGHT_RECT.contains(p)) \
                    and self.snipDirection == node.HORIZONTAL:
                    
                    if self.allSpouses - self.hiddenSpouses > 0:
                        self.panel.appState.snip(self.personID,
                                                 [self.panel.appState.ped.HUSBAND_TO_WIFE,
                                                  self.panel.appState.ped.WIFE_TO_HUSBAND])
                    elif self.allSpouses > 0:
                        self.panel.appState.expand(self.personID,
                                   set(self.panel.appState.ped.iterSpouses(self.personID)))
                elif node.BOTTOM_RECT.contains(p) and self.snipDirection == node.DOWN:
                    
                    if self.allChildren - self.hiddenChildren > 0:
                        self.panel.appState.snip(self.personID,
                                                 [self.panel.appState.ped.PARENT_TO_CHILD])
                    elif self.allSpouses > 0:
                        self.panel.appState.expand(self.personID,
                                   set(self.panel.appState.ped.iterChildren(self.personID)))
            else:
                # TODO: reorder the nodes
                pass

class ghostNode(object):
    def __init__(self, generation, chunk, index, parent, child):
        self.generation = generation
        self.chunk = chunk
        self.index = index
        self.parent = parent
        self.child = child
        self.targetX = 0
        self.targetY = 0
    
    def x(self):
        return self.targetX
    
    def y(self):
        return self.targetY

class pedigreeSlice(fadeableGraphicsItem):
    OPACITY_PROPORTION = 0.5
    THICKNESS = 5
    
    def __init__(self, x, y, height, brush):
        fadeableGraphicsItem.__init__(self, x, y)
        self.height = height
        self.brush = brush
        self.setZValue(4)
    
    def boundingRect(self):
        return QRectF(-pedigreeSlice.THICKNESS*0.5,-self.height*0.5,pedigreeSlice.THICKNESS,self.height)
    
    def paint(self, painter, option, widget=None):
        painter.setOpacity(self.opacity*pedigreeSlice.OPACITY_PROPORTION)
        painter.fillRect(-pedigreeSlice.THICKNESS*0.5,-self.height*0.5,pedigreeSlice.THICKNESS,self.height,self.brush)

class pedigreeLabel(fadeableGraphicsItem):
    BOUNDING_BOX = QRectF(-200,-100,400,200)
    FONT = QFont('Helvetica',24)
    OPACITY_PROPORTION = 0.5
    
    def __init__(self, text, color, x, y):
        fadeableGraphicsItem.__init__(self, x, y)
        self.text = text
        self.pen = QPen(color)
        self.setZValue(2)
    
    def boundingRect(self):
        return pedigreeLabel.BOUNDING_BOX
    
    def paint(self, painter, option, widget=None):
        painter.setOpacity(self.opacity*pedigreeLabel.OPACITY_PROPORTION)
        painter.setFont(pedigreeLabel.FONT)
        painter.setPen(self.pen)
        painter.fillRect(pedigreeLabel.BOUNDING_BOX,Qt.black)
        painter.drawText(pedigreeLabel.BOUNDING_BOX,Qt.AlignHCenter | Qt.AlignVCenter,self.text)

class edgeLayer(QGraphicsItem):
    MARRIAGE_PEN = QPen(Qt.black, 1.0, Qt.DotLine)
    NORMAL_PEN = QPen(Qt.black, 1.0, Qt.SolidLine)
    
    def __init__(self, panel):
        QGraphicsItem.__init__(self)
        self.panel = panel
        self.setZValue(1)
    
    def boundingRect(self):
        return QRectF(0.0,0.0,self.panel.right,self.panel.bottom)
    
    def getLastNodes(self,g):
        lastNodes = {}
        for chunk in xrange(3):
            for n in self.panel.generations[g][chunk]:
                p = n
                while isinstance(p,ghostNode):
                    p = p.parent
                if not isinstance(n,ghostNode):
                    n = self.panel.nodes[n]
                lastNodes[p] = n
        return lastNodes
    
    def paint(self, painter, option, widget=None):
        painter.fillRect(0,0,self.panel.right,self.panel.bottom,self.panel.appState.BACKGROUND_COLOR)
        
        lastNodes = None
        for g in self.panel.generationOrder:
            if g in self.panel.emptyGenerations:
                continue
            elif lastNodes == None:
                lastNodes = self.getLastNodes(g)
                continue
            finishedLocalArcs = set()
            for chunk in xrange(3):
                for n1 in self.panel.generations[g][chunk]:
                    p1 = n1
                    while isinstance(p1,ghostNode):
                        p1 = p1.child
                    if not isinstance(n1,ghostNode):
                        n1 = self.panel.nodes[p1]
                    for p2,linkType in self.panel.appState.ped.iterNuclear(p1):
                        if linkType == self.panel.appState.ped.HUSBAND_TO_WIFE or \
                           linkType == self.panel.appState.ped.WIFE_TO_HUSBAND:
                            edgeLayer.MARRIAGE_PEN.setColor(self.panel.appState.getPathColor(p1,p2))
                            painter.setPen(edgeLayer.MARRIAGE_PEN)
                        else:
                            edgeLayer.NORMAL_PEN.setColor(self.panel.appState.getPathColor(p1,p2))
                            painter.setPen(edgeLayer.NORMAL_PEN)
                        
                        if (p2,p1) not in finishedLocalArcs:
                            if p2 in self.panel.generations[g][0] or \
                               p2 in self.panel.generations[g][1] or \
                               p2 in self.panel.generations[g][2]:
                                n2 = self.panel.nodes[p2]
                                painter.drawLine(n1.x(),n1.y(),n2.x(),n2.y())
                                finishedLocalArcs.add((p1,p2))
                        if lastNodes.has_key(p2):
                            n2 = lastNodes[p2]
                            color = self.panel.appState.getPathColor(p1,p2)
                            painter.setPen(QPen(color, 1.5, self.panel.appState.getPathPattern(p1,p2)))
                            painter.drawLine(n1.x(),n1.y(),n2.x(),n2.y())
            lastNodes = self.getLastNodes(g)

class PedigreeComponent(AppComponent):
    FRAME_DURATION = 1000/60 # 60 FPS
    
    def __init__(self, view, appState):
        self.view = view
        self.appState = appState
        self.appState.registerComponent(self)
        
        self.nodes = {}
        self.corpses = set()
        
        self.generations = {}
        self.generationOrder = []
        self.emptyGenerations = set()
        
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        # TODO: figure out these sizes differently...
        self.bottom = 500
        self.right = 1800
        
        # Background
        self.edges = edgeLayer(self)
        self.scene.addItem(self.edges)
        
        # Slices
        self.aSlice = pedigreeSlice(self.right,self.bottom/2,self.bottom,
                                    self.appState.MISSING_COLOR)
        self.scene.addItem(self.aSlice)
        self.aSlice.hide()
        
        self.bSlice = pedigreeSlice(self.right,self.bottom/2,self.bottom,
                                    self.appState.MISSING_COLOR)
        self.scene.addItem(self.bSlice)
        self.bSlice.hide()
        
        # Labels
        self.aLabel = pedigreeLabel("Pedigree A",self.appState.A_COLOR,
                                    self.right,self.bottom/2)
        self.scene.addItem(self.aLabel)
        self.aLabel.hide()
        
        self.bLabel = pedigreeLabel("Pedigree B",self.appState.B_COLOR,
                                    self.right,self.bottom/2)
        self.scene.addItem(self.bLabel)
        self.bLabel.hide()
        
        self.iLabel = pedigreeLabel("A "+unichr(8745)+" B",self.appState.INTERSECTION_COLOR,
                                    self.right,self.bottom/2)
        self.scene.addItem(self.iLabel)
        self.iLabel.hide()
        
        # TODO: add some buttons for union, intersection, and closing A and B
        
        self.timer = QTimer(self.view)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(PedigreeComponent.FRAME_DURATION)
    
    def addCorpse(self,i):
        self.corpses.add(i)
    
    def dumpCorpses(self):
        self.corpses = set()
    
    def notifyHighlightAnIndividual(self, previous, new):
        if self.nodes.has_key(previous):
            self.nodes[previous].highlightedExternally = False
            self.nodes[previous].prepareGeometryChange()
        if self.nodes.has_key(new):
            self.nodes[new].highlightedExternally = True
            self.nodes[new].prepareGeometryChange()
    
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
            newGenerations[g] = ([],[],[])
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
            elif not self.nodes[p].killed:
                raise Exception('Attempted to add a node to the view that isn\'t in either set A or B!')
        self.generationOrder = sorted(self.generations.iterkeys())
        
        # Now we need to know which generations actually have people in them, and which relationships span more than one generation
        numGenerations = 0
        self.emptyGenerations = set()
        relationshipsThatNeedGhosts = {}
        for g1 in self.generationOrder:
            if len(self.generations[g1][0]) > 0 or len(self.generations[g1][1]) > 0 or len(self.generations[g1][2]) > 0:
                numGenerations += 1
                for c1,chunk in enumerate(self.generations[g1]):
                    for i1, p1 in enumerate(chunk):
                        for p2,linkType in self.appState.ped.iterNuclear(p1):  # @UnusedVariable
                            g2 = self.appState.ped.getAttribute(p2,'generation')
                            if abs(g2-g1) > 1 and not relationshipsThatNeedGhosts.has_key((p2,p)):
                                if p2 in self.appState.abIntersection:
                                    i2 = self.generations[g2][1].index(p2)
                                    c2 = 1
                                elif p2 in self.appState.aSet:
                                    i2 = self.generations[g2][0].index(p2)
                                    c2 = 0
                                elif p2 in self.appState.bSet:
                                    i2 = self.generations[g2][2].index(p2)
                                    c2 = 2
                                else:
                                    assert not self.nodes.has_key(p2) or self.nodes[p2].killed
                                    continue
                                relationshipsThatNeedGhosts[(p,p2)] = (g1,c1,i1,g2,c2,i2)
            else:
                self.emptyGenerations.add(g1)
        
        if numGenerations == 0:
            # at this point we know for sure there is no data currently displayed
            return
        
        # Now determine where ghosts need to be created by interpolating list indices linearly
        ghosts = {}
        for (p1,p2),(g1,c1,i1,g2,c2,i2) in relationshipsThatNeedGhosts.iteritems():
            start = self.generationOrder.index(g1)
            stop = self.generationOrder.index(g2)
            if stop < start:
                # switch all our variables
                temp = start
                start = stop
                stop = temp
                
                temp = p1
                p1 = p2
                p2 = temp
                
                temp = g1
                g1 = g2
                g2 = temp
                
                temp = c1
                c1 = c2
                c2 = temp
                
                temp = i1
                i1 = i2
                i2 = temp
            
            generationsNeedingGhosts = []
            for g in self.generationOrder[start+1:stop]:
                if g not in self.emptyGenerations:
                    generationsNeedingGhosts.append(g)
            if len(generationsNeedingGhosts) == 0:
                continue
            
            spanningIndex1 = i1
            temp = c1
            while temp > 0:
                temp = temp-1
                spanningIndex1 += len(self.generations[g1][temp])
            spanningIndex2 = i2
            temp = c2
            while temp > 0:
                temp = temp-1
                spanningIndex2 += len(self.generations[g2][temp])
            indexIncrement = 1.0/len(generationsNeedingGhosts)*(spanningIndex2-spanningIndex1)
            
            lastGhost = p1
            for n,g in enumerate(generationsNeedingGhosts):
                targetIndex = int(spanningIndex1 + (n+0.5)*indexIncrement)
                targetChunk = 0
                while targetChunk < 2 and targetIndex >= len(self.generations[g][targetChunk]):
                    targetIndex -= len(self.generations[g][targetChunk])
                    targetChunk += 1
                newGhost = ghostNode(g, targetChunk, targetIndex, lastGhost, p2)
                if isinstance(lastGhost,ghostNode):
                    lastGhost.child = newGhost
                ghosts[newGhost] = (g,targetChunk,targetIndex)
                
        # Now add the ghosts where they're supposed to go
        for ghost,(g,c,i) in ghosts.iteritems():
            self.generations[g][c].insert(i,ghost)
        
        # Now update screen targets; first we need to know the widest generation in each section
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
        
        # set the slice, label target positions, as well as the spacing between each node
        yincrement = (self.bottom-node.EXPANDED_RADIUS*2)/max(numGenerations-1,2)
        # a two-generation pedigree across the top and bottom looks funny... use the middle
        # for pedigrees of low depth (and width in xincrement). This also prevents division
        # by 0 problems
        if numNonEmpty > 1:
            xincrement = (self.right-node.EXPANDED_RADIUS*2)/max(aWidth+iWidth+bWidth+1,2)  
            # the extra width is for the slices
            
            self.aSlice.targetX = aWidth*xincrement
            self.bSlice.targetX = (aWidth+1+iWidth)*xincrement
            self.aLabel.targetX = self.aSlice.targetX / 2
            self.iLabel.targetX = self.aSlice.targetX + (self.aSlice.targetX+self.bSlice.targetX)/2
            self.bLabel.targetX = (self.bSlice.targetX + self.right)/2
            self.aSlice.show()
            self.bSlice.show()
            self.aLabel.show()
            self.iLabel.show()
            self.bLabel.show()
        else:
            xincrement = (self.right-node.EXPANDED_RADIUS*2)/max(aWidth+iWidth+bWidth-1,2)
            for item in [self.aSlice,self.bSlice,self.aLabel,self.bLabel,self.iLabel]:
                item.targetX = self.right
                item.hide()
        
        # set the node target positions
        y = node.EXPANDED_RADIUS   # start with an offset; nodes are drawn from the center
        for g in self.generationOrder:
            if g in self.emptyGenerations:
                continue
            a,i,b = self.generations[g]
            
            # align a to the left
            x = node.EXPANDED_RADIUS
            for p in a:
                if isinstance(p,ghostNode):
                    item = p
                else:
                    item = self.nodes[p]
                item.targetX = x
                item.targetY = y
                x += xincrement
            
            # TODO: align i to the center
            x = node.EXPANDED_RADIUS + (aWidth)*xincrement
            if numNonEmpty > 1:
                x += xincrement     # space for the slice
            
            for p in i:
                if isinstance(p,ghostNode):
                    item = p
                else:
                    item = self.nodes[p]
                item.targetX = x
                item.targetY = y
                x += xincrement
            
            # TODO: align b to the right
            x = node.EXPANDED_RADIUS + (aWidth+iWidth)*xincrement
            if numNonEmpty > 1:
                x += xincrement*2   # space for the slices
            for p in b:
                if isinstance(p,ghostNode):
                    item = p
                else:
                    item = self.nodes[p]
                item.targetX = x
                item.targetY = y
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
    
    def minimizeCrossings(self, iterations=10):
        pass
    
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
        
        self.minimizeCrossings()
        
        self.scene.update()