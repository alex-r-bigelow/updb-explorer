import sys, os, traceback
from PySide.QtGui import QApplication, QMessageBox, QFileDialog, QProgressDialog
from PySide.QtCore import Qt, QFile
from PySide.QtUiTools import QUiLoader
from resources.pedigree_data import Pedigree, gexf_node_attribute_mapper

NUM_TICKS = 100
visWindow = None

class cancelException(Exception):
    pass

class loading(object):
    def __init__(self):
        self.loader = QUiLoader()
        infile = QFile("resources/loading.ui")
        infile.open(QFile.ReadOnly)
        self.window = self.loader.load(infile, None)
        infile.close()
        
        self.overrides = {'personID':self.window.personID,
                         'paID':self.window.paID,
                         'maID':self.window.maID,
                         'sex':self.window.sex,
                         'affected':self.window.affected,
                         'n_local_aff':self.window.n_local_aff,
                         'n_local_desc':self.window.n_local_desc,
                         'nicki_d':self.window.nicki_d,
                         'is_root':self.window.is_root,
                         'is_leaf':self.window.is_leaf,
                         'generation':self.window.generation}
        self.requiredForCalculateD = set(['personID','paID','maID','sex','affected'])
        self.header = []
        self.lowerHeader = []
        
        self.window.browseInputButton.clicked.connect(self.browseInput)
        self.window.inputField.textChanged.connect(self.switchPrograms)
        self.window.browseOutputButton.clicked.connect(self.browseOutput)
        self.window.outputField.textChanged.connect(self.switchPrograms)
        self.window.programBox.currentIndexChanged.connect(self.switchPrograms)
        self.window.runButton.clicked.connect(self.go)
        
        self.switchPrograms()
        self.window.buttonBox.setEnabled(False)
        
        self.window.show()
    
    def displayError(self, message, details=None):
        msgBox = QMessageBox()
        msgBox.setText(message)
        msgBox.setIcon(QMessageBox.Critical)
        if details != None:
            msgBox.setDetailedText(details)
        msgBox.exec_()
    
    def browseInput(self):
        fileName = QFileDialog.getOpenFileName(caption=u"Open file")[0]
        self.window.inputField.setText(fileName)
        self.switchPrograms()
    
    def switchPrograms(self):
        currentProgram = self.window.programBox.currentText()
        if currentProgram == 'calculateD':
            enableButtonBox = os.path.exists(self.window.inputField.text()) and os.path.exists(os.path.split(self.window.outputField.text())[0])
            self.window.outputArea.setEnabled(True)
            self.window.generateLabel.show()
        else:
            enableButtonBox = os.path.exists(self.window.inputField.text())
            self.window.outputArea.setEnabled(False)
            self.window.generateLabel.hide()
        
        fileName = self.window.inputField.text()
        if not os.path.exists(fileName):
            self.window.buttonBox.setEnabled(False)
            for d,b in self.overrides.iteritems():
                text = b.currentText()
                b.clear()
                if text != "":
                    b.setEditText(text)
            self.header = []
            self.lowerHeader = []
        else:
            with open(fileName,'rb') as infile:
                self.header = infile.readline().strip().split('\t')
                for h in self.header:
                    self.lowerHeader.append(h.lower())
            infile.close()
            for d,b in self.overrides.iteritems():
                text = b.currentText()
                b.clear()
                b.addItems(self.header)
                if text != "":
                    b.setEditText(text)
                    '''if text not in self.header:
                        if d in self.requiredForCalculateD:
                            enableButtonBox = False
                        elif currentProgram == 'vis':
                            enableButtonBox = False'''
                elif d in self.header:
                    b.setEditText(d)
                elif d.lower() in self.lowerHeader:
                    b.setEditText(self.header[self.lowerHeader.index(d.lower())])
                else:
                    b.setEditText('')
                    '''if d in self.requiredForCalculateD:
                        enableButtonBox = False
                    elif currentProgram == 'vis':
                        enableButtonBox = False'''
            self.window.buttonBox.setEnabled(enableButtonBox)
    
    def browseOutput(self):
        fileName = QFileDialog.getSaveFileName(caption=u"Save file")[0]
        self.window.outputField.setText(fileName)
        self.switchPrograms()
    
    def go(self):
        global visWindow
        for k in Pedigree.REQUIRED_KEYS.keys():
            t = self.overrides[k].currentText()
            if t == '':
                self.displayError("%s header is required." % k)
                return
            elif not t in self.header:
                self.displayError("%s doesn't exist in the input file." % t)
                return
            Pedigree.REQUIRED_KEYS[k] = t
        for k in Pedigree.RESERVED_KEYS.keys():
            t = self.overrides[k].currentText()
            if self.window.programBox.currentText() == 'vis':
                if t == '':
                    self.displayError("%s header is required." % k)
                    return
                elif not t in self.header:
                    self.displayError("%s doesn't exist in the input file." % t)
                    return
            else:
                if t == '':
                    t = k
            Pedigree.RESERVED_KEYS[k] = t
        
        try:
            if self.window.programBox.currentText() == 'vis':
                fileName = self.window.inputField.text()
                if fileName.lower().endswith('.gexf') or fileName.lower().endswith('.json'):
                    raise Exception('.gexf and .json formats are not supported for the vis program. Use calculateD to create a .dat file.')
                ped = Pedigree(fileName, countAndCalculate=False, zeroMissing=self.window.zeroMissingBox.isChecked())
                from resources.main_app import App
                self.window.hide()
                visWindow = App(ped)
                self.window.close()
            else:
                progress = QProgressDialog(u"Running...", u"Cancel", 0, NUM_TICKS, parent=None)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                
                def tick(newMessage=None, increment=1):
                    if progress.wasCanceled():
                        raise cancelException('Cancel clicked.')
                    newValue = min(progress.maximum(),progress.value()+increment)
                    progress.setValue(newValue)
                    if newMessage != None:
                        progress.setLabelText(newMessage)
                    return True
                
                ped = Pedigree(self.window.inputField.text(), countAndCalculate=True, zeroMissing=self.window.zeroMissingBox.isChecked(), tickFunction=tick, numTicks=NUM_TICKS)
                
                progress.setLabelText('Writing File...')
                extension = os.path.splitext(self.window.outputField.text())[1].lower()
                if extension == '.gexf':
                    edgeTypes = Pedigree.defaultEdgeTypes()
                    nodeAttributeTypes = Pedigree.defaultNodeAttributeTypes()
                    nodeAttributeTypes['is_root'] = gexf_node_attribute_mapper('is_root', attrType=gexf_node_attribute_mapper.BOOLEAN, defaultValue=False, validValues=[False,True])
                    ped.write_gexf(self.window.outputField.text(), edgeTypes, nodeAttributeTypes)
                elif extension == '.json':
                    ped.write_json(self.window.outputField.text())
                else:
                    ped.write_egopama(self.window.outputField.text())
                
                progress.close()
                
                self.window.inputField.setText(self.window.outputField.text())
                self.window.outputField.setText("")
                self.window.programBox.setCurrentIndex(1)
        except Exception, e:
            if not isinstance(e, cancelException):
                self.displayError("An unexpected error occurred.",traceback.format_exc())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = loading()
    app.exec_()