import sys, serial, gui

def log(*msgs, sep=' ', end='\n'):
    print('[serialImpl.py]', *msgs, sep=sep, end=end)

def getAvailableSpeeds():
    return [ '9600', '38400', '115200' ]

def getAvailableSerials():
        platformName = sys.platform
        
        if platformName.startswith('win'):
            ports = [ 'COM%s' % (i + 1) for i in range(256) ]
        elif platformName.startswith('linux') or platformName.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        else:
            raise EnvironmentError('Платформа не поддерживается')

        available = [ "None" ]
        for portName in ports:
            try:
                port = serial.Serial(portName)
                port.close()
                available.append(portName)
            except (OSError, serial.SerialException):
                pass
        
        return available
        
def getString(serialPort, decodeCharset):
    return serialPort.readline().decode(decodeCharset)

def tryReadLine(serialPort, readSize):
    return serialPort.read(size=readSize);
    
def tryReadSizeFromSymbol(serialPort, startSymbol, readSize):
    readedSymbol = serialPort.read()
    while readedSymbol[0] != ord(startSymbol):
        readedSymbol = serialPort.read()
    return serialPort.read(size=readSize-1)
    
def getString(bytes_array, decodeCharset):
    return bytes_array.decode(decodeCharset);

def connectTo(name, speed, timeout_sec, errorCallback):
    serialPort = None
    
    try:
        serialPort = serial.Serial(name, speed, timeout=timeout_sec)
        serialPort.flushInput()
        log('Успешно открыт порт %s!' % serialPort.name)
    except Exception as e:
        log(e)
        errorCallback(e)
    
    return serialPort

def close(serialPort):
    if serialPort == None:
        log('Нечего закрывать! Последовательный порта не существует!')
        return 0
    
    if serialPort.isOpen():
        serialPort.close()
        log('%s закрыт.' % serialPort.name)
        return 1