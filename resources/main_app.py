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
        self.window.historyDataSplitter.insertWidget(0,self.tableWidget)
        self.window.historyDataSplitter.update()
        
        # Add our pedigree view with its settings widgets
        settingsWidgets = {'canvasWidth':self.window.canvasWidth,
                           'canvasHeight':self.window.canvasHeight}
        self.pedigreeView = PedigreeComponent(settingsWidgets, self.state)
        self.window.pedigreeSplitter.insertWidget(0,self.pedigreeView)
        self.window.pedigreeSplitter.update()
        
        self.window.showMaximized()
        #self.window.showFullScreen()
    
def run(ped):
    app = QApplication(sys.argv)
    window = App(ped)  # @UnusedVariable
    return app.exec_()