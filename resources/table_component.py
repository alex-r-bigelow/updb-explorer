from PySide.QtGui import QBrush, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QCursor
from PySide.QtCore import Qt
from app_state import AppComponent

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
            painter.fillRect(rect,self.parent().appState.getColorForValue(0.0,self.parent().horizontalHeaderItem(logicalIndex).text()))
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            table = self.parent()
            attr = table.horizontalHeaderItem(table.column(table.itemAt(event.pos()))).text()
            table.appState.showAttributeMenu(attr)
        else:
            QHeaderView.mouseReleaseEvent(self,event)

class TableComponent(QTableWidget,AppComponent):
    def __init__(self, appState):
        QTableWidget.__init__(self)
        self.appState = appState
        self.appState.registerComponent(self)
        
        self.headerObj = CustomHeader(Qt.Horizontal, self)
        self.setHorizontalHeader(self.headerObj)
        
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(True)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        self.numColumns = 0
        self.idLookup = {}
        
        # Load data
        self.setColumnCount(len(self.appState.headers))
        self.setRowCount(len(self.appState.ped.rowOrder))
        self.setHorizontalHeaderLabels(self.appState.headers)
        for r,p in enumerate(self.appState.ped.rowOrder):
            idItem = PythonTableWidgetItem(p)
            self.setItem(r,0,idItem)
            self.idLookup[p] = idItem
            for c,a in enumerate(self.appState.ped.extraNodeAttributes):
                self.setItem(r,c+1,PythonTableWidgetItem(self.appState.ped.getAttribute(p,a,None)))
    
    def setItem(self, row, column, item):
        QTableWidget.setItem(self,row,column,item)
        item.setBackground(self.appState.MISSING_COLOR)
        self.numColumns = max(column,self.numColumns)
    
    def colorRow(self, person, color=None):
        row = self.row(self.idLookup[person])
        if color == None:
            if person == self.appState.highlightedNode:
                color = self.appState.HIGHLIGHT_COLOR
            elif person in self.appState.abIntersection:
                color = self.appState.INTERSECTION_COLOR
            elif person in self.appState.aSet:
                color = self.appState.A_COLOR
            elif person in self.appState.bSet:
                color = self.appState.B_COLOR
            else:
                color = self.appState.MISSING_COLOR
        for c in xrange(self.numColumns+1):
            self.item(row,c).setBackground(QBrush(color))
    
    def notifyChangeOverlay(self, previous, new):
        self.headerObj.overlayIndex = new
        pIndex = None
        nIndex = None
        for i in xrange(self.numColumns):
            t = self.horizontalHeaderItem(i).text()
            if t == previous:
                pIndex = i
            if t == new:
                nIndex = i
        
        self.headerObj.overlayIndex = nIndex
        
        if pIndex != None:
            self.headerObj.updateSection(pIndex)
        if nIndex != None:
            self.headerObj.updateSection(nIndex)
    
    def notifyHighlightAnIndividual(self, previous, new):
        if previous != None:
            self.colorRow(previous)
        if new != None:
            self.colorRow(new)
    
    def notifyChangePedigreeA(self, previousID, newID):
        previousSet = self.appState.getHistoryPeople(previousID)
        newSet = self.appState.getHistoryPeople(previousID)
        
        for p in previousSet.symmetric_difference(newSet):  # only have to recolor stuff that changed
            self.colorRow(p)
    
    def notifyChangePedigreeB(self, previousID, newID):
        previousSet = self.appState.getHistoryPeople(previousID)
        newSet = self.appState.getHistoryPeople(previousID)
        
        for p in previousSet.symmetric_difference(newSet):  # only have to recolor stuff that changed
            self.colorRow(p)
    
    def mouseReleaseEvent(self, event):
        m = event.button()
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        if m == Qt.RightButton:
            self.appState.showIndividualContextMenu(currentID)
    
    def mouseDoubleClickEvent(self, event):
        m = event.button()
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        if m == Qt.LeftButton:
            self.appState.showIndividualDetails(currentID)
    
    def mouseMoveEvent(self, event):
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        self.appState.highlightAnIndividual(currentID)
    
    def leaveEvent(self, event):
        self.appState.highlightAnIndividual(None)