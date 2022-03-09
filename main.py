#COM-parser code

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
import sys, threading, gui
import serialImpl as impl
import pyqtgraph as graph

# Serial port settings
SERIAL_DECODE_CHARSET = 'utf-8'
SERIAL_TIMEOUT_SEC = 2

# in dev...
def log(*msgs, sep=' ', end='\n'):
    print(*msgs, sep=sep, end=end)

class Signals(QtCore.QObject):
    log('Loaded signals')
    updatePlotSignal = QtCore.pyqtSignal(int, str)

class Main(QMainWindow, gui.Ui_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.signals = Signals()
        self.plotScreen = PlotScreen()
        self.signals.updatePlotSignal.connect(self.plotScreen.updatePlot)
        
        self.currentPort = None
        self.listenThread = None
        self.xCounter = 0
        
        # add events
        self.updateSerialsAction.triggered.connect(self.updateSerialSettingsEvent)
        self.graphAction.triggered.connect(self.openPlotScreenEvent)
        self.connectButton.clicked.connect(self.connectToSerialEvent)
        self.serialPorts.currentTextChanged.connect(self.toggleConnectButtonEvent)
        log('Added GUI events')
        # initial update serial settings
        self.updateSerialSettingsEvent()
        log('Serial settings updated')
    
    def toggleConnectButtonEvent(self, newText):
        self.connectButton.setEnabled(newText != 'None')
    
    def closeEvent(self, event):
        if self.currentPort:
            self.closeSerialEvent()
    
    def handleData(self, dataStr):
        # any handle of data (filter, write to console/file/plot...)
        self.signals.updatePlotSignal.emit(self.xCounter, dataStr)
        self.xCounter += 1;
        pass
    
    def listenPort(self):
        log('Start listening %s' % self.currentPort.name)
        while self.portListening:
            if self.currentPort.inWaiting() > 0:
                self.handleData(impl.getString(
                                    self.currentPort,
                                    SERIAL_DECODE_CHARSET))
    
    def updateSerialSettingsEvent(self):
        self.serialPorts.clear()
        self.serialSpeeds.clear()
        self.serialPorts.addItems(impl.getAvailableSerials())
        self.serialSpeeds.addItems(impl.getAvailableSpeeds())

    def connectToSerialEvent(self):
        self.currentPort = impl.connectTo(
                                self.serialPorts.currentText(),
                                self.serialSpeeds.currentText(),
                                SERIAL_TIMEOUT_SEC)
        
        if self.currentPort:
            self.portListening = True
            self.listenThread = threading.Thread(None, self.listenPort)
            self.listenThread.start()
            
            # update button state connect->close
            button = self.connectButton
            button.setText('Close')
            connectStatus = self.connectStatus
            connectStatus.setText('Opened')
            connectStatus.setStyleSheet('color: rgb(0, 220, 0);')
            # swap button events
            action = self.connectButton.clicked
            action.disconnect(self.connectToSerialEvent)
            action.connect(self.closeSerialEvent)

    def closeSerialEvent(self):
        self.portListening = False
        log('Stop listening %s' % self.currentPort.name)
        if impl.close(self.currentPort):
            self.currentPort = None
            
            # update button state close->connect
            button = self.connectButton
            button.setText('Connect')
            connectStatus = self.connectStatus
            connectStatus.setText('Closed')
            connectStatus.setStyleSheet('color: rgb(220, 0, 0);')
            # swap button events
            action = self.connectButton.clicked
            action.disconnect(self.closeSerialEvent)
            action.connect(self.connectToSerialEvent)

    def openPlotScreenEvent(self):
        self.plotScreen.show()
        log('Display plot screen')

import random as rand

class PlotScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flag = False
        self.graphs = []
        self.x = []
        self.y = []
        self.arr = []
        
        self.setWindowTitle('New plot')
        log('Loaded plot screen')

        self.graph = graph.PlotWidget()
        self.setCentralWidget(self.graph)

        self.graph.setBackground('#000000')
        self.graph.setTitle('New graph', color='#66EE88', size='20px')
        labelStyle = {
            'color': '#00DDAA',
            'font-size': '15px'
        }
        self.graph.setLabel('left', 'Row', **labelStyle)
        self.graph.setLabel('bottom', 'Column', **labelStyle)
        self.graph.addLegend()

        self.graph.showGrid(x=False, y=True)
        self.graph.setYRange(0, 256, padding=0)

    def closeEvent(self, event):
        log('Plot screen closed')

    def plot(self, x, y, name, color):
        pen = graph.mkPen(color=color, width=4)
        return self.graph.plot(x, y, name=name, pen=pen)
    
    def updatePlot(self, xCounter, serialString):
        valArr = serialString.split(',')
        
        if self.flag == False:
            for val in valArr:
                color = (rand.randint(64, 255),
                         rand.randint(64, 255),
                         rand.randint(64, 255))
                self.graphs.append(self.plot([], [], val, color))
                self.x.append([])
                self.y.append([])
            self.flag = True
            log('Created %d plots' % len(self.graphs))
        
        for i in range(len(self.graphs)):
            if len(self.y[i]) >= 300:
                self.x[i] = self.x[i][1:]
                self.y[i] = self.y[i][1:]

            try:
                valArr[i] = float(valArr[i])
                self.x[i].append(xCounter)
                self.y[i].append(valArr[i])
            except ValueError as e:
                pass

            self.graphs[i].setData(self.x[i], self.y[i])
                
        #log('plot', serialString, end='')

app = QApplication(sys.argv)
window = Main()
window.show()
sys.exit(app.exec())
