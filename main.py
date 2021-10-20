#COM-parser code

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
import sys, threading, time
import serial
import pyqtgraph as graphs
import gui
import numpy as np

class Signals(QtCore.QObject):
    updateGraphSignal = QtCore.pyqtSignal(int, float)

class SerialUtils():
    def updateSerials():
        ports = []

        platformName = sys.platform
        
        if platformName.startswith('win'):
            ports = [ 'COM%s' % (i + 1) for i in range(256) ]
        elif platformName.startswith('linux') or platformName.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        else:
            raise EnvironmentError('Unsupported platform')

        available = [ "None" ]
        for portName in ports:
            try:
                port = serial.Serial(portName)
                port.close()
                available.append(portName)
            except (OSError, serial.SerialException):
                pass
        
        return available

    def getString(serialPort):
        return serialPort.readline().decode('ASCII')

class SerialListener():
    def __init__(self, main):
        self.main = main
    
    def connect(self):
        self.serialPort = None
        
        try:
            self.serialPort = serial.Serial(self.main.serialPorts.currentText(), self.main.serialSpeeds.currentText())
            print('Connected successfully to %s!' % self.serialPort.name)

            self.listening = True
            self.listenThread = threading.Thread(None, self.listen)
            self.listenThread.start()
            
            return 1
        except Exception as e:
            print(e)
        
        return 0

    def close(self):
        if self.serialPort == None:
            print('Nothing to be closed! Serial port doesn\'t exists!')
            return 0
        
        if self.serialPort.isOpen():
            self.listening = False
            
            self.serialPort.close()
            print('%s closed.' % self.serialPort.name)
            
            self.serialPort = None
            return 1

    def listen(self):
        xCounter = 0

        signals = Signals()
        signals.updateGraphSignal.connect(self.main.graphWindow.updateGraph)
        
        while self.listening:
            if self.serialPort.inWaiting() > 0:
                rxString = SerialUtils.getString(self.serialPort)
                
                if self.main.graphWindow != None:
                    # emit signal about updating graph to MAIN THREAD
                    signals.updateGraphSignal.emit(xCounter, float(rxString))
                    
                    xCounter += 1
            time.sleep(0.25)

class GraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Graph')
        print('Open graph window')
        
        self.graph = graphs.PlotWidget()
        self.setCentralWidget(self.graph)

        self.xLine = []
        self.yLine = []

        # plot data: x, y values
        self.graph.setBackground('#000000')
        color = (255, 0, 0)
        lineWidth = 4
        graphPen = graphs.mkPen(color, width=lineWidth)

        self.graph.setTitle('Graph 1', color='#66EE88', size='20px')
        labelStyle = {
            'color' : '#00DDAA',
            'font-size' : '15px'
        }
        self.graph.setLabel('left', 'ADC value', **labelStyle)
        self.graph.setLabel('bottom', 'Time, ms', **labelStyle)

        self.graph.addLegend()

        self.graph.showGrid(x=False, y=True)
        self.graph.setYRange(0, 1024, padding=0.45)
        self.graph.disableAutoRange(axis='y')
        
        self.graphLine = self.graph.plot(self.xLine, self.yLine, name='ADC value', pen=graphPen)

    def updateGraph(self, x, y):
        if len(self.xLine) > 50:
            self.xLine = self.xLine[1:]
            self.yLine = self.yLine[1:]
            
        self.xLine.append(x)
        self.yLine.append(y)

        self.graphLine.setData(self.xLine, self.yLine)

class ImportSettingsDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Import Settings')
        self.resize(300, 200)
        self.setModal(True)

class Main(QMainWindow, gui.Ui_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.guiInit()
        # setup classes
        self.serialListener = SerialListener(self)
        # windows classes
        self.graphWindow = None
    
    def guiInit(self):
        # add events
        self.updateSerialsAction.triggered.connect(self.updateSerialsEvent)
        self.graphAction.triggered.connect(self.graphWindowEvent)
        self.importSettingsAction.triggered.connect(self.importSettingsEvent)
        self.connectButton.clicked.connect(self.connectSerialEvent)
        # configure gui elements
        self.updateSerialsEvent()
        self.serialSpeeds.addItems([ '9600', '38400', '115200' ])

    def graphWindowEvent(self):
        if self.graphWindow == None:
            # one instance in program
            self.graphWindow = GraphWindow()
        
        self.graphWindow.show()

    def importSettingsEvent(self):
        self.importSettingsDialog = ImportSettingsDialog()
        self.importSettingsDialog.show()

    def updateSerialsEvent(self):
        self.serialPorts.clear()
        self.serialPorts.addItems(SerialUtils.updateSerials())

    def connectSerialEvent(self):
        if self.serialListener.connect():

            # update button state connect->close
            button = self.connectButton
            button.setText('Close')
            connectStatus = self.connectStatus
            connectStatus.setText('Opened')
            connectStatus.setStyleSheet('color: rgb(0, 220, 0);')
            # swap button events
            action = self.connectButton.clicked
            action.disconnect(self.connectSerialEvent)
            action.connect(self.closeSerialEvent)

    def closeSerialEvent(self):
        if self.serialListener.close():
            
            # update button state close->connect
            button = self.connectButton
            button.setText('Connect')
            connectStatus = self.connectStatus
            connectStatus.setText('Closed')
            connectStatus.setStyleSheet('color: rgb(220, 0, 0);')
            # swap button events
            action = self.connectButton.clicked
            action.disconnect(self.closeSerialEvent)
            action.connect(self.connectSerialEvent)
    
app = QApplication(sys.argv)
window = Main()
window.show()
sys.exit(app.exec())
