import sys
from PySide.QtGui import QApplication
from PySide.QtCore import QFile
from PySide.QtUiTools import QUiLoader
from app_state import AppState
from pedigree_component import PedigreeComponent
from table_component import TableComponent

class App(object):
    def __init__(self, ped):
        self.state = AppState(ped)
        
        self.loader = QUiLoader()
        infile = QFile("resources/vis.ui")
        infile.open(QFile.ReadOnly)
        self.window = self.loader.load(infile, None)
        infile.close()
        
        # Add our custom table
        self.tableWidget = TableComponent(self.state)
        self.window.lowSplitter.insertWidget(0,self.tableWidget)
        self.window.lowSplitter.update()
        
        # Add our pedigree view
        self.pedigreeView = PedigreeComponent(self.window.pedigreeView, self.state)
        
        self.window.showMaximized()
        #self.window.showFullScreen()
    
def run(ped):
    app = QApplication(sys.argv)
    window = App(ped)  # @UnusedVariable
    return app.exec_()