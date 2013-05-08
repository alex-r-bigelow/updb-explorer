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
            column = table.horizontalHeaderItem(table.column(table.itemAt(event.pos()))).text()
            m = QMenu()
            m.addAction('Overlay/Filter')
            c = m.addMenu('Compare to')
            for h in table.appState.headers:
                c.addAction(h)
            m.addAction('Sort...')
            choice = m.exec_(QCursor.pos())
            
            if choice != None:
                choice = choice.text()
                if choice == 'Overlay/Filter':
                    table.appState.changeOverlay(column)
                elif choice == 'Sort...':
                    # TODO
                    pass
                else:
                    table.appState.changeScatterplot(choice,column)
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
        item.setBackground(self.appState.BACKGROUND_COLOR)
        self.numColumns = max(column,self.numColumns)
    
    def colorRow(self, row, color):
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
    
    def notifyChangeHighlightedNode(self, previous, new):
        if self.appState.secondRoot != None and previous == self.appState.secondRoot:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.SECOND_ROOT_COLOR)
        elif self.appState.root != None and previous == self.appState.root:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.ROOT_COLOR)
        elif previous != None:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.BACKGROUND_COLOR)
        
        if new != None:
            self.colorRow(self.row(self.idLookup[new]),self.appState.HIGHLIGHT_COLOR)
    
    def notifySetRoot(self, previous, prevSet, new, newSet):
        if self.appState.highlightedNode != None and previous == self.appState.highlightedNode:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.HIGHLIGHT_COLOR)
        elif self.appState.secondRoot != None and previous == self.appState.secondRoot:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.SECOND_ROOT_COLOR)
        elif previous != None:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.BACKGROUND_COLOR)
        
        if new != None:
            self.colorRow(self.row(self.idLookup[new]),self.appState.ROOT_COLOR)
            self.scrollToItem(self.idLookup[new])
    
    def notifyShowSecondRoot(self, previous, prevSet, new, newSet):
        if self.appState.highlightedNode != None and previous == self.appState.highlightedNode:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.HIGHLIGHT_COLOR)
        elif self.appState.root != None and previous == self.appState.root:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.ROOT_COLOR)
        elif previous != None:
            self.colorRow(self.row(self.idLookup[previous]),self.appState.BACKGROUND_COLOR)
        
        if new != None:
            self.colorRow(self.row(self.idLookup[new]),self.appState.SECOND_ROOT_COLOR)
            self.scrollToItem(self.idLookup[new])
        
    def mouseDoubleClickEvent(self, event):
        m = event.button()
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        if m == Qt.LeftButton:
            self.appState.showSecondRoot(currentID)
    
    def mouseMoveEvent(self, event):
        currentRow = self.rowAt(event.y())
        currentID = self.item(currentRow,0).sortKey
        
        self.appState.changeHighlightedNode(currentID)
    
    def leaveEvent(self, event):
        self.appState.changeHighlightedNode(None)