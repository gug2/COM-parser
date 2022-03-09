import sys, serial, gui

def getAvailableSpeeds():
    return [ '9600', '38400', '115200' ]

def getAvailableSerials():
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
        
def getString(serialPort, decodeCharset):
    return serialPort.readline().decode(decodeCharset)

def connectTo(name, speed, timeout_sec):
    serialPort = None
    
    try:
        serialPort = serial.Serial(name, speed, timeout=timeout_sec)
        serialPort.flushInput()
        print('Successfully connected to %s!' % serialPort.name)
    except Exception as e:
        print(e)
    
    return serialPort

def close(serialPort):
    if serialPort == None:
        print('Nothing to be closed! Serial port doesn\'t exists!')
        return 0
    
    if serialPort.isOpen():
        serialPort.close()
        print('%s closed.' % serialPort.name)
        return 1