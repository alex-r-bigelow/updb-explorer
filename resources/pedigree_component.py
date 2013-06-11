import random, math, networkx
from PySide.QtGui import QGraphicsScene, QGraphicsItem, QPen, QPainterPath, QFont
from PySide.QtCore import Qt, QRectF, QTimer
from app_state import AppComponent
import sys

class fadeableGraphicsItem(QGraphicsItem):
    '''
    A visual screen object that keeps track of its own position and opacity; this guy
    is responsible for all the animation. updateValues() should be called periodically
    '''
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
    '''
    Graphical representation of a person in the pedigree
    '''
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
    '''
    A placeholder in our generations structure; the dot paper calls these "virtual" nodes
    '''
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
    '''
    The physical divider between segments of our pedigree
    '''
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
    '''
    The label that floats in the background to tell us which pedigree is which
    '''
    BOUNDING_BOX = QRectF(-400,-400,800,800)
    FONT = QFont('Helvetica',128)
    OPACITY_PROPORTION = 0.25
    
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
        painter.drawText(pedigreeLabel.BOUNDING_BOX,Qt.AlignHCenter | Qt.AlignVCenter,self.text)

class edgeLayer(QGraphicsItem):
    '''
    The thing that's responsible for drawing the connections between every non-killed node
    '''
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
    
    def drawLine(self, painter, p1, p2, x1, y1, x2, y2):
        linkType = self.panel.appState.ped.getLink(p1,p2)
        if linkType == self.panel.appState.ped.HUSBAND_TO_WIFE or \
           linkType == self.panel.appState.ped.WIFE_TO_HUSBAND:
            edgeLayer.MARRIAGE_PEN.setColor(self.panel.appState.getPathColor(p1,p2))
            painter.setPen(edgeLayer.MARRIAGE_PEN)
        else:
            edgeLayer.NORMAL_PEN.setColor(self.panel.appState.getPathColor(p1,p2))
            painter.setPen(edgeLayer.NORMAL_PEN)
        
        painter.drawLine(x1,y1,x2,y2)
    
    def paint(self, painter, option, widget=None):
        painter.fillRect(0,0,self.panel.right,self.panel.bottom,self.panel.appState.BACKGROUND_COLOR)
        
        finishedGhostNodes = set()
        finishedEdges = set()
        
        for n in self.panel.iterGenerations():
            if isinstance(n,ghostNode):
                if n in finishedGhostNodes:
                    continue
                # get the ancestor and descendant so we know what type of line to draw
                p = n.parent
                c = n.child
                while isinstance(p,ghostNode):
                    p = p.parent
                while isinstance(c,ghostNode):
                    c = c.child
                
                # start with the highest relationship
                n2 = n
                while isinstance(n2.parent,ghostNode):
                    n2 = n2.parent
                
                # work all the way down
                while isinstance(n2.child,ghostNode):
                    pn = n2.parent
                    if not isinstance(pn,ghostNode):
                        pn = self.panel.nodes[pn]
                    self.drawLine(painter,p,c,pn.x(),pn.y(),n2.x(),n2.y())
                    finishedGhostNodes.add(n2)
                    n2 = n2.child
                
                # for the last one, we need to draw both the parent and child lines
                pn = n2.parent
                if not isinstance(pn,ghostNode):
                    pn = self.panel.nodes[pn]
                self.drawLine(painter,p,c,pn.x(),pn.y(),n2.x(),n2.y())
                cn = self.panel.nodes[n2.child] # we already know the child isn't a ghostNode
                self.drawLine(painter,p,c,n2.x(),n2.y(),cn.x(),cn.y())
                finishedGhostNodes.add(n2)
            else:
                for n2 in self.panel.iterGenerationsFrom(person=n,
                                                         directions=[node.DOWN,node.HORIZONTAL],
                                                         relationships=None,
                                                         level=1,
                                                         skipFirst=True,
                                                         yieldGhosts=False):
                    pn = self.panel.nodes[n]
                    cn = self.panel.nodes[n2]
                    if (pn,cn) in finishedEdges or (cn,pn) in finishedEdges:
                        continue
                    self.drawLine(painter, n, n2, pn.x(), pn.y(), cn.x(), cn.y())
                    finishedEdges.add((pn,cn))
            
class PedigreeComponent(AppComponent):
    FRAME_DURATION = 1000/60 # 60 FPS
    
    def __init__(self, view, appState):
        self.view = view
        self.appState = appState
        self.appState.registerComponent(self)
        
        self.nodes = {}
        self.corpses = set()    # A bug in PySide doesn't allow us to just throw
                                # away items once they've been removed from the
                                # scene; we have to hold on to a reference for a
                                # while or we'll get a seg fault
        
        # This is our big ugly structure that is responsible for sorting nodes;
        # it looks like this: {generation number: ([a],[i],[b])}
        # where a is the list/"chunk" of people in that generation that are in
        # self.appState.aSet, etc.
        self.generations = {}
        # Generations are not necessarily well-behaved; we use this list for iterating in order
        self.generationOrder = []
        # If we want to know where a person lives in our structure, this is:
        # {person: (generation number, chunk number 0-2, index in that chunk)
        self.generationLookup = {}
        # We also need to know in several places the relationships between individuals
        # that are in our generations
        self.generationNetwork = networkx.DiGraph()
        # These are the maximum widths of each chunk; useful when drawing
        self.aWidth = 0
        self.iWidth = 0
        self.bWidth = 0
        # A flag that tells us we should bother trying to rearrange the orders
        # within the chunks
        self.rearrange = True
        
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
        self.aLabel = pedigreeLabel("A",self.appState.A_COLOR,
                                    self.right,self.bottom/2)
        self.scene.addItem(self.aLabel)
        self.aLabel.hide()
        
        self.bLabel = pedigreeLabel("B",self.appState.B_COLOR,
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
        # Keep everyone in the same order that hasn't been killed or moved; also ignore ghost nodes for now
        oldPeople = set()
        movedFromA = set()
        movedFromIntersection = set()
        movedFromB = set()
        newGenerations = {}
        for g in self.generationOrder:
            a,i,b = self.generations[g]
            newGen = ([],[],[])
            hasData = False
            for p in a:
                if not isinstance(p,ghostNode) and not self.nodes[p].killed:
                    hasData = True
                    if p in self.appState.aSet and p not in self.appState.abIntersection:
                        oldPeople.add(p)
                        newGen[0].append(p)
                    else:
                        movedFromA.add(p)
            for p in i:
                if not isinstance(p,ghostNode) and not self.nodes[p].killed:
                    hasData = True
                    if p in self.appState.abIntersection:
                        oldPeople.add(p)
                        newGen[1].append(p)
                    else:
                        movedFromIntersection.add(p)
            for p in b:
                if not isinstance(p,ghostNode) and not self.nodes[p].killed:
                    hasData = True
                    if p in self.appState.bSet and not p in self.appState.abIntersection:
                        oldPeople.add(p)
                        newGen[2].append(p)
                    else:
                        movedFromB.add(p)
            if hasData:
                newGenerations[g] = newGen
        self.generations = newGenerations
        
        # Now add everyone that is new, as well as people that were moved to new areas
        for p in self.nodes.iterkeys():
            if p in oldPeople or not self.nodes.has_key(p) or self.nodes[p].killed:
                continue
            g = self.appState.ped.getAttribute(p,'generation')
            if not self.generations.has_key(g):
                self.generations[g] = ([],[],[])
            if p in self.appState.aSet and not p in self.appState.abIntersection:
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
            elif p in self.appState.bSet and not p in self.appState.abIntersection:
                if p in movedFromIntersection or p in movedFromA:
                    self.generations[g][2].insert(0,p)  # moved people shoudl start on the left
                else:
                    self.generations[g][2].append(p)    # new people should start on the right
            elif not self.nodes[p].killed:
                raise Exception('Attempted to add a node to the view that isn\'t in either set A or B!')
        self.generationOrder = sorted(self.generations.iterkeys())
        
        if len(self.generations) == 0:
            # at this point we know for sure there is no data currently displayed
            return
        
        # Now we need to know which relationships span more than one generation
        relationshipsThatNeedGhosts = {}
        for g1 in self.generationOrder:
            assert len(self.generations[g1][0]) > 0 or len(self.generations[g1][1]) > 0 or len(self.generations[g1][2]) > 0
            for c1,chunk in enumerate(self.generations[g1]):
                for i1, p1 in enumerate(chunk):
                    for p2,linkType in self.iterLivingNuclear(p1, strict=True):  # @UnusedVariable
                        g2 = self.appState.ped.getAttribute(p2,'generation')
                        if abs(g2-g1) > 1 and \
                           not relationshipsThatNeedGhosts.has_key((p2,p1)) and \
                           not relationshipsThatNeedGhosts.has_key((p1,p2)):
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
                                print p2
                                sys.exit(1)
                            relationshipsThatNeedGhosts[(p1,p2)] = (g1,c1,i1,g2,c2,i2)
        
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
                generationsNeedingGhosts.append(g)
            if len(generationsNeedingGhosts) == 0:
                continue
            
            spanningIndex1 = i1
            if c1 >= 1:
                spanningIndex1 += len(self.generations[g1][0])
            if c1 == 2:
                spanningIndex1 += len(self.generations[g1][1])
            
            spanningIndex2 = i2
            if c2 >= 1:
                spanningIndex2 += len(self.generations[g2][0])
            if c2 == 2:
                spanningIndex2 += len(self.generations[g2][1])
            indexIncrement = float(spanningIndex2-spanningIndex1)/len(generationsNeedingGhosts)
            
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
        
        # Update our convenience structures
        self.indexGenerations()
        
        # Finally, update stuff on the screen
        self.updateScreenPositions()
        self.rearrange = True
    
    def indexGenerations(self):
        '''
        builds convenience structures for lookups / traversal our complicated generation dict
        '''
        self.generationLookup = {}
        self.generationNetwork = networkx.DiGraph()
        widths = [0,0,0]
        lastRow = set()
        for g in self.generationOrder:
            chunks = self.generations[g]
            currentRow = set()
            currentRow.update(chunks[0])
            currentRow.update(chunks[1])
            currentRow.update(chunks[2])
            for chunkNo,chunk in enumerate(chunks):
                widths[chunkNo] = max(len(chunk),widths[chunkNo])
                for index,p in enumerate(chunk):
                    self.generationLookup[p] = (g,chunkNo,index)
                    self.generationNetwork.add_node(p)
                    if isinstance(p,ghostNode):
                        ancestor = p.parent
                        while isinstance(ancestor,ghostNode):
                            ancestor = ancestor.parent
                        descendant = p.child
                        while isinstance(descendant,ghostNode):
                            descendant = descendant.child
                        downLink = self.appState.ped.getLink(ancestor,descendant)
                        upLink = self.appState.ped.getLink(descendant,ancestor)
                        
                        self.generationNetwork.add_edge(p,p.parent,{'dir':node.UP,'link':upLink})
                        self.generationNetwork.add_edge(p.parent,p,{'dir':node.DOWN,'link':downLink})
                        self.generationNetwork.add_edge(p,p.child,{'dir':node.DOWN,'link':downLink})
                        self.generationNetwork.add_edge(p.child,p,{'dir':node.UP,'link':upLink})
                    else:
                        for p2,linkType in self.iterLivingNuclear(p, strict=True):
                            assert self.appState.ped.getLink(p,p2) != None
                            self.generationNetwork.add_edge(p,p2,{'link':linkType})
                            if p2 in lastRow:
                                self.generationNetwork.add_edge(p,p2,{'dir':node.UP})
                                self.generationNetwork.add_edge(p2,p,{'dir':node.DOWN})
                            elif p2 in currentRow:
                                self.generationNetwork.add_edge(p,p2,{'dir':node.HORIZONTAL})
                                self.generationNetwork.add_edge(p2,p,{'dir':node.HORIZONTAL})
            lastRow = currentRow
        self.aWidth = widths[0]
        self.iWidth = widths[1]
        self.bWidth = widths[2]
    
    def refreshHiddenCounts(self):
        '''
        Each node needs to know how many people are visible next to it
        '''
        for a in self.nodes.iterkeys():
            self.nodes[a].hiddenParents = self.nodes[a].allParents
            self.nodes[a].hiddenChildren = self.nodes[a].allChildren
            self.nodes[a].hiddenSpouses = self.nodes[a].allSpouses
            for b,l in self.iterLivingNuclear(a, strict=True):  # @UnusedVariable
                if l == self.appState.ped.PARENT_TO_CHILD:
                    self.nodes[a].hiddenChildren -= 1
                elif l == self.appState.ped.CHILD_TO_PARENT:
                    self.nodes[a].hiddenParents -= 1
                else:
                    self.nodes[a].hiddenSpouses -= 1
    
    def iterLivingNuclear(self, person, strict=False):
        '''
        Helper function independent of our convenience structures (it's used to create the
        generations dict and convenience structures in the first place)
        '''
        if not self.nodes.has_key(person) or self.nodes[person].dead or (strict and self.nodes[person].killed):
            raise StopIteration
        else:
            for b,l in self.appState.ped.iterNuclear(person):
                if not self.nodes.has_key(b) or self.nodes[b].dead or (strict and self.nodes[b].killed):
                    continue
                yield (b,l)
    
    def iterGenerationsFrom(self, person, directions=None, relationships=None, level=1, skipFirst=True, yieldGhosts=True):
        '''
        BFS among generation elements, only in the specified directions (generation space)
        and/or relationships (pedigree space)
        '''
        if directions == None:
            directions = [node.UP,
                          node.DOWN,
                          node.HORIZONTAL]
        if relationships == None:
            relationships = [self.appState.ped.PARENT_TO_CHILD,
                             self.appState.ped.CHILD_TO_PARENT,
                             self.appState.ped.HUSBAND_TO_WIFE,
                             self.appState.ped.WIFE_TO_HUSBAND]
        # BFS only along specified directions and relationships
        toVisit = [(person,0)]
        visited = set()
        while len(toVisit) > 0:
            p,l = toVisit.pop(0)
            if p not in visited:
                visited.add(p)
                if not isinstance(p,ghostNode):
                    for p2,attrs in self.generationNetwork.edge[p].iteritems():
                        assert isinstance(p2,ghostNode) or self.appState.ped.getLink(p,p2) != None
                        if not attrs.has_key('dir') or not attrs['dir'] in directions or not attrs['link'] in relationships:
                            continue
                        if l < level:
                            toVisit.append((p2,l+1))
                if (p != person or not skipFirst) and (not isinstance(p,ghostNode) or yieldGhosts):
                    yield p
    
    def iterGenerations(self):
        for g in self.generationOrder:
            for chunk in self.generations[g]:
                for p in chunk:
                    yield p
    
    def updateScreenPositions(self):
        numNonEmpty = 0
        if self.aWidth > 0:
            numNonEmpty += 1
        if self.iWidth > 0:
            numNonEmpty += 1
        if self.bWidth > 0:
            numNonEmpty += 1
        
        # set the slice, label target positions, as well as the spacing between each node
        yincrement = (self.bottom-node.EXPANDED_RADIUS*2)/max(len(self.generations)-1,2)
        # a two-generation pedigree across the top and bottom looks funny... use the middle
        # for pedigrees of low depth (and width in xincrement). This also prevents division
        # by 0 problems
        if numNonEmpty > 1:
            xincrement = (self.right-node.EXPANDED_RADIUS*2)/max(self.aWidth+self.iWidth+self.bWidth+1,2)  
            # the extra width is for the slices
            
            self.aSlice.targetX = self.aWidth*xincrement
            self.bSlice.targetX = (self.aWidth+1+self.iWidth)*xincrement
            self.aLabel.targetX = self.aSlice.targetX / 2
            self.iLabel.targetX = (self.aSlice.targetX+self.bSlice.targetX)/2
            self.bLabel.targetX = (self.bSlice.targetX + self.right)/2
            self.aSlice.show()
            self.bSlice.show()
            self.aLabel.show()
            self.iLabel.show()
            self.bLabel.show()
        else:
            xincrement = (self.right-node.EXPANDED_RADIUS*2)/max(self.aWidth+self.iWidth+self.bWidth-1,2)
            for item in [self.aSlice,self.bSlice,self.aLabel,self.bLabel,self.iLabel]:
                item.targetX = self.right
                item.hide()
            if self.aWidth > 0:
                self.aLabel.targetX = self.right/2
                self.aLabel.show()
            elif self.iWidth > 0:
                self.iLabel.targetX = self.right/2
                self.iLabel.show()
            elif self.bWidth > 0:
                self.bLabel.targetX = self.right/2
                self.bLabel.show()
        
        # set the node target positions
        y = node.EXPANDED_RADIUS   # start with an offset; nodes are drawn from the center
        for g in self.generationOrder:
            a,i,b = self.generations[g]
            
            # TODO: align to the widest row - for now I align in the center
            aCenterSpace = (self.aWidth-len(a))*xincrement/2
            iCenterSpace = (self.iWidth-len(i))*xincrement/2
            bCenterSpace = (self.bWidth-len(b))*xincrement/2
            
            x = node.EXPANDED_RADIUS + aCenterSpace
            for p in a:
                if isinstance(p,ghostNode):
                    item = p
                else:
                    item = self.nodes[p]
                item.targetX = x
                item.targetY = y
                x += xincrement
            
            x = node.EXPANDED_RADIUS + (self.aWidth)*xincrement + iCenterSpace
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
            
            x = node.EXPANDED_RADIUS + (self.aWidth+self.iWidth)*xincrement + bCenterSpace
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
    
    def medianValue(self, neighbors):
        neighbors.sort()
        m = int(len(neighbors)/2)
        if len(neighbors) == 0:
            return -1.0
        elif len(neighbors) % 2 == 1:
            return neighbors[m]
        elif len(neighbors) == 2:
            return (neighbors[0]+neighbors[1])/2.0
        else:
            left = neighbors[m-1]-neighbors[0]
            right = neighbors[-1]-neighbors[m]
            return (neighbors[m-1]*right + neighbors[m]*left)/(left+right)
    
    def barycentricValue(self, neighbors):
        if len(neighbors) == 0:
            return -1.0
        else:
            return sum(neighbors)/float(len(neighbors))
    
    def countCrossings(self, person):
        '''
        Counts the number of edges that cross; relies heavily on the convenience structures
        '''
        totalCrossings = 0
        # secondary sort by index
        parents = sorted(self.iterGenerationsFrom(person,
                                                  directions=[node.UP],
                                                  relationships=None,
                                                  level=1,
                                                  skipFirst=True,
                                                  yieldGhosts=True),
                         key=lambda parent: self.generationLookup[parent][2])
        if len(parents) == 0:
            return 0
        # primary sort by chunk number
        parents = sorted(parents, key=lambda parent: self.generationLookup[parent][1])
        
        # we need every person in the last generation in between the leftmost parent and the rightmost one
        parentSpanPeeps = []
        gen = self.generationLookup[parents[0]][0]
        chunk = self.generationLookup[parents[0]][1]
        index = self.generationLookup[parents[0]][2]
        while chunk <= self.generationLookup[parents[-1]][1] and chunk < 3:
            while index <= self.generationLookup[parents[-1]][2] and index < len(self.generations[gen][chunk]):
                parentSpanPeeps.append(self.generations[gen][chunk][index])
                index += 1
            index = 0
            chunk += 1
        
        parents = set(parents)
        
        myChunk = self.generationLookup[person][1]
        myIndex = self.generationLookup[person][2]
        
        for p2 in parentSpanPeeps:
            numParentsToTheLeft = 0
            numParentsToTheRight = len(parents)
            if p2 in parents:
                numParentsToTheLeft += 1
                numParentsToTheRight -= 1
            else:
                # we need to know the number of children of this unrelated person to the left and right of person
                unrelatedLeftNeighbors = 0
                unrelatedRightNeighbors = 0
                for p3 in self.iterGenerationsFrom(p2,
                                                   directions=[node.DOWN],
                                                   relationships=None,
                                                   level=1,
                                                   skipFirst=True,
                                                   yieldGhosts=True):
                    if self.generationLookup[p3][1] < myChunk:
                        unrelatedLeftNeighbors += 1
                    elif self.generationLookup[p3][1] > myChunk:
                        unrelatedRightNeighbors += 1
                    else:
                        assert self.generationLookup[p3][2] != myIndex
                        if self.generationLookup[p3][2] < myIndex:
                            unrelatedLeftNeighbors += 1
                        elif self.generationLookup[p3][2] > myIndex:
                            unrelatedRightNeighbors += 1
                totalCrossings += numParentsToTheLeft * unrelatedLeftNeighbors + \
                                  numParentsToTheRight * unrelatedRightNeighbors
        return totalCrossings
    
    def countAllCrossings(self):
        totalCrossings = 0
        for p in self.iterGenerations():
            totalCrossings += self.countCrossings(p)
        return totalCrossings
    
    def minimizeCrossings(self, iterations=9, startTop=True):
        newGenerations = {}
        maxCrossings = float('inf')
        triedOnce = False
        for iterNo in xrange(iterations):  # @UnusedVariable
            if startTop:
                gOrder = self.generationOrder
            else:
                gOrder = reversed(self.generationOrder)
            
            # First sort the indices using the dot layout median weighting scheme
            for g in gOrder:
                newChunks = [[],[],[]]
                for chunkNo,chunk in enumerate(self.generations[g]):
                    weights = {}
                    for p in chunk:
                        neighbors = self.iterGenerationsFrom(p,
                                                             directions=[node.UP,node.HORIZONTAL],
                                                             relationships=None,
                                                             level=1,
                                                             skipFirst=True,
                                                             yieldGhosts=True)
                        indices = []
                        for n in neighbors:
                            spanningIndex = self.generationLookup[n][2]
                            if self.generationLookup[n][1] >= 1:
                                spanningIndex += self.aWidth
                            if self.generationLookup[n][1] == 2:
                                spanningIndex += self.iWidth
                            indices.append(spanningIndex)
                        weights[p] = self.barycentricValue(indices)
                    newChunks[chunkNo] = sorted(chunk, key=lambda p: weights[p])
                newGenerations[g] = tuple(newChunks)
                
            # TODO: transpose step
            
            oldGenerations = self.generations
            oldGenerationOrder = self.generationOrder
            oldGenerationLookup = self.generationLookup
            oldGenerationNetwork = self.generationNetwork
            oldAWidth = self.aWidth
            oldIWidth = self.iWidth
            oldBWidth = self.bWidth
            
            self.generations = newGenerations
            self.generationOrder = sorted(self.generations.keys())
            self.indexGenerations()
            
            crossings = self.countAllCrossings()
            if crossings < maxCrossings:
                maxCrossings = crossings
                triedOnce = False
            else:
                self.generations = oldGenerations
                self.generationOrder = oldGenerationOrder
                self.generationLookup = oldGenerationLookup
                self.generationNetwork = oldGenerationNetwork
                self.aWidth = oldAWidth
                self.iWidth = oldIWidth
                self.bWidth = oldBWidth
                
                if not triedOnce:
                    triedOnce = True
                else:
                    self.rearrange = False
                    return
            startTop = not startTop # alternate top to bottom and bottom to top
    
    def updateValues(self):
        self.aSlice.updateValues()
        self.bSlice.updateValues()
        self.aLabel.updateValues()
        self.iLabel.updateValues()
        self.bLabel.updateValues()
        
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
        
        if self.rearrange:
            self.minimizeCrossings()
            self.updateScreenPositions()
        
        self.scene.update()