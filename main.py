#COM-parser code

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog,QPushButton,QGraphicsProxyWidget
import sys, threading, gui
import serialImpl as SERIAL_IMPL
import packetDecoder as PACKET_DECODER
import pyqtgraph as PY_QT_GRAPH
import random as RAND
import os
import time, datetime
# настройки COM порта
SERIAL_DECODE_CHARSET = 'utf-8'
SERIAL_TIMEOUT_SEC = 2
SERIAL_PACKET_SIZE = 60
ENABLED_PLOTS = [1, 3, 4, 6]
ENABLED_PLOTS_NAMES = ['STLM temp', 'MS alt', 'BMP alt', 'photo']

globalSerialBuffer = []

def log(*msgs, sep=' ', end='\n'):
    print('[main.py]', *msgs, sep=sep, end=end)

def ms(ns):
    return ns / 1000 / 1000

class Signals(QtCore.QObject):
    log('Сигналы загружены')
    updatePlotSignal = QtCore.pyqtSignal(str)

class Main(QMainWindow, gui.Ui_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.signals = Signals()
        self.plotScreen = PlotScreen()
        self.packetDecoder = PACKET_DECODER.PacketDecoder(self.plotScreen.delimiter)
        self.signals.updatePlotSignal.connect(self.plotScreen.updatePlot)
        
        self.currentPort = None
        self.listenThread = None
        self.rxCounter = 0
        self.damageCounter = 0
        
        # добавляем события
        self.updateSerialsAction.triggered.connect(self.updateSerialSettingsEvent)
        self.graphAction.triggered.connect(self.openPlotScreenEvent)
        self.connectButton.clicked.connect(self.connectToSerialEvent)
        self.serialPorts.currentTextChanged.connect(self.toggleConnectButtonEvent)
        self.delimiterEdit.clicked.connect(self.delimiterEditEvent)
        self.delimiterSave.clicked.connect(self.delimiterSaveEvent)
        log('Добавлены события GUI элементов')
        # поиск доступных COM портов
        self.updateSerialSettingsEvent()
    
    def toggleConnectButtonEvent(self, newText):
        self.connectButton.setEnabled(newText != 'None')

    def displayError(self, errorMessage):
        self.errorMsg.setText(str(errorMessage))
        self.errorMsg.setToolTip(str(errorMessage))
        
    def closeEvent(self, event):
        if self.currentPort:
            self.closeSerialEvent()

    def handleData2(self, encodedBytes):
        log('прочитано ->', encodedBytes)

        if encodedBytes[SERIAL_PACKET_SIZE-2] == ord('\n'):
            #log('ok')
            self.rxCounter += 1

            # буфферизация
            globalSerialBuffer.append(encodedBytes)
        else:
            #log('damaged')
            self.damageCounter += 1

        self.rxCounterValue.setText('RX: %d / %d' % (self.rxCounter, self.damageCounter))
        self.rxCounterValue.setToolTip(self.rxCounterValue.text())

        pass
        
    def decodeDataThread(self):
        global globalSerialBuffer
        
        toSend = ''
        while self.portListening:
            while len(globalSerialBuffer) > 0:
                toSend = self.packetDecoder.decodeData(globalSerialBuffer[0])
                globalSerialBuffer = globalSerialBuffer[1:]
        
#TODO!!!  -- запись в лог всех декодированных данных --
                LOG_TO_FILE_START_NS = time.time_ns()
                with open('last_log.csv', 'a') as logFile:
                    logFile.write(str(datetime.datetime.now()) + '-> ' + toSend + '\n')
                LOG_TO_FILE_TIME_NS = time.time_ns() - LOG_TO_FILE_START_NS
                #log('запись в файл[ms]', ms(LOG_TO_FILE_TIME_NS))
#TODO!!!
        


                # обработка данных (фильтры, запись в консоль/файл/график...)
                self.signals.updatePlotSignal.emit(toSend)
            time.sleep(0.001)
    
    def listenPort(self):
        while self.portListening:
            try:
                if self.currentPort.inWaiting() > 0:
# TODO !!
                    self.handleData2(SERIAL_IMPL.tryReadSizeFromSymbol(self.currentPort, '$', SERIAL_PACKET_SIZE))
# TODO !!
                time.sleep(0.001)
            except Exception as e:
                # закрываем порт
                self.closeSerialEvent()

                # отображаем ошибку
                log(e)
                self.displayError(e)
                return
    
    def updateSerialSettingsEvent(self):
        self.closeSerialEvent()
        
        self.serialPorts.clear()
        self.serialSpeeds.clear()
        self.serialPorts.addItems(SERIAL_IMPL.getAvailableSerials())
        self.serialSpeeds.addItems(SERIAL_IMPL.getAvailableSpeeds())

        log('COM-порты обновлены')
    
    def connectToSerialEvent(self):
        # открытый порт уже существует
        if self.currentPort:
            return
        
        self.currentPort = SERIAL_IMPL.connectTo(
                                self.serialPorts.currentText(),
                                self.serialSpeeds.currentText(),
                                SERIAL_TIMEOUT_SEC, self.displayError)
        
        if self.currentPort:
            self.startListening(self.currentPort)

            self.listenThread = threading.Thread(None, self.listenPort)
            self.listenThread.start()
            
            self.decodeThread = threading.Thread(None, self.decodeDataThread)
            self.decodeThread.start()

            # пересоздаем графики
            self.plotScreen.recreatePlots()
            self.rxCounter = 0
            self.damageCounter = 0
            
            
            # обновляем состояние кнопки connect->close
            button = self.connectButton
            button.setText('Откл.')
            connectStatus = self.connectStatus
            connectStatus.setText('Доступен')
            connectStatus.setStyleSheet('color: rgb(0, 220, 0);')
            # меняем событие для кнопки connect->close
            action = self.connectButton.clicked
            action.disconnect(self.connectToSerialEvent)
            action.connect(self.closeSerialEvent)

    def closeSerialEvent(self):
        # если порта нет - нечего закрывать
        if not self.currentPort:
            return
        
        self.stopListening(self.currentPort)
        
        if SERIAL_IMPL.close(self.currentPort):
            self.currentPort = None
            
            # обновляем состояние кнопки close->connect
            button = self.connectButton
            button.setText('Подкл.')
            connectStatus = self.connectStatus
            connectStatus.setText('Закрыт')
            connectStatus.setStyleSheet('color: rgb(220, 0, 0);')
            # меняем событие для кнопки close->connect
            action = self.connectButton.clicked
            action.disconnect(self.closeSerialEvent)
            action.connect(self.connectToSerialEvent)

    def openPlotScreenEvent(self):
        self.plotScreen.show()
        log('Открыто окно графика')

    def delimiterEditEvent(self):
        # меняем состояния кнопок
        self.delimiterValue.setEnabled(True)
        self.delimiterEdit.setEnabled(False)
        self.delimiterSave.setEnabled(True)
    
    def delimiterSaveEvent(self):
        if not self.delimiterValue.text():
            
            # выдаем предупреждение
            self.delimiterWarningMsg.setText('разделитель должен быть не пустой!');
            return
        
        if self.plotScreen.delimiter != self.delimiterValue.text():
            # устанавливаем новый разделитель
            self.plotScreen.delimiter = self.delimiterValue.text()

            # очищаем предупреждение, если оно было
            self.delimiterWarningMsg.setText('новый разделитель: \"' + self.plotScreen.delimiter + '\"')

        # добавляем кавычки
        self.delimiterValue.setText('[' + self.delimiterValue.text() + ']')
        # меняем состояния кнопок
        self.delimiterValue.setEnabled(False)
        self.delimiterEdit.setEnabled(True)
        self.delimiterSave.setEnabled(False)

    def startListening(self, port):
        self.portListening = True
        log('Прослушиваем  %s' % port.name)

    def stopListening(self, port):
        self.portListening = False
        log('Прекратили прослушивать %s' % port.name)

class PlotScreen(QMainWindow):
    def __init__(self, ):
        super().__init__()
        self.isPlotsCreated = False
        self.delimiter = ','
        self.x = []
        self.y = []
        self.plots = []
        
        self.setWindowTitle('Графики')
        log('Окно графика загружено')

        self.layout = PY_QT_GRAPH.GraphicsLayoutWidget()
        self.setCentralWidget(self.layout)
        
        self.gpsInfo = self.layout.addLabel(row=0,col=0,colspan=2)
        self.gpsInfo.setText('latlon', **{'color':'#00DDAA','size':'25px'}) 
        

    def closeEvent(self, event):
        log('Окно графика скрыто')

    def recreatePlots(self):
        if self.isPlotsCreated:
            # запускаем процесс пересоздания графиков
            self.isPlotsCreated = False
            # очищаем список графиков
            self.plots.clear()
            # очищаем массивы данных
            self.x.clear()
            self.y.clear()

            self.layout.clear()
            log('Окно графиков очищено')
    
    def updatePlot(self, serialString):
        PLOT_DRAW_START_NS = time.time_ns()
        
        dataArray = serialString.split(self.delimiter)

        if not dataArray:
            return
        
        # обновляем данные графиков
        if self.isPlotsCreated:
            #if len(self.x) >= 10:
            #    self.x = self.x[1:]

            # x axis - received time in ms
            self.x.append(int(dataArray[0]))

            # add gps info
            labelStyle = {
                'color': '#00DDAA',
                'size': '25px'
            }
            self.gpsInfo.setText(dataArray[7]+'/'+dataArray[8], **labelStyle)
            
            for i in range(len(self.plots)):
                if i not in ENABLED_PLOTS:
                    continue
                #if len(self.y[i]) >= 10:
                #    self.y[i] = self.y[i][1:]

                try:
                    dataArray[i] = float(dataArray[i])
                    self.y[i].append(dataArray[i])
                except ValueError as e:
                    self.y[i].append(self.y[i][-1])
                
                self.plots[i].dataObject.setData(self.x, self.y[i])

        # пересоздаем графики
        if self.isPlotsCreated == False:
            self.isPlotsCreated = True
            
            graphNamesIndex = 0

            row = 1
            col = 0
            for i in range(len(dataArray)):
                if i not in ENABLED_PLOTS:
                    self.plots.append(None)
                    self.y.append([])
                    continue
                
                self.plots.append(PlotSeparatableObject(self.layout, ENABLED_PLOTS_NAMES[graphNamesIndex], row, col))
                graphNamesIndex += 1

                self.y.append([])
                if col < 4/2-1:
                    col += 1
                else:
                    col = 0
                    row += 1
            
            log('Создано %d графиков' % len(self.plots))
        
        PLOT_DRAW_TIME_NS = time.time_ns() - PLOT_DRAW_START_NS
        log('отрисовка графиков[ms]', ms(PLOT_DRAW_TIME_NS))

class PlotSeparatableObject():
    def __init__(self, _layout, _name, _row, _column):
        self.layoutObject = _layout
        self.plotObject = self.createPlot(_name, _row, _column)
        self.dataObject = self.createData(self.plotObject, _name)

        #self.separateButton = QPushButton(self.layoutObject)
        #self.separateButton.setGeometry(QtCore.QRect(_row*30, _column*30, 20, 20))
        #self.separateButton.setText('[]')
        #self.separateButton.clicked.connect(self.separate)
    
    def createPlot(self, _name, _row, _column):
        plot = self.layoutObject.addPlot(row=_row, col=_column)

        plot.setTitle(_name, color='66EE88', size='20px')

        labelStyle = {
            'color': '#00DDAA',
            'font-size': '15px'
        }
        plot.setLabel('left', 'ось X', **labelStyle)
        plot.setLabel('bottom', 'ось Y', **labelStyle)
        plot.addLegend()

        plot.showGrid(x=False, y=True)
        plot.setYRange(0, 256, padding=0)

        # автоматическое масштабирование кривой в окне графика
        plot.enableAutoRange()

        return plot

    def createData(self, plotObject, dataName):
        # задаем случайный цвет графику
        _color = ( RAND.randint(64, 255), RAND.randint(64, 255), RAND.randint(64, 255) )
        _width = 4
        
        _pen = PY_QT_GRAPH.mkPen(color=_color, width=_width)
        
        return plotObject.plot([], [], name=dataName, pen=_pen)

    def separate(self):
        log('separate plot', self.plotObject)
    
# запуск приложения
app = QApplication(sys.argv)
window = Main()
window.show()
sys.exit(app.exec())

