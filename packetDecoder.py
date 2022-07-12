import time

def log(*msgs, sep=' ', end='\n'):
    print('[packetDecoder.py]', *msgs, sep=sep, end=end)

def ms(ns):
    return ns / 1000 / 1000

class PacketDecoder():
    def __init__(self, _delimiter):
        self.delimiter = _delimiter
        self.lastU32 = 0
        self.lastI32 = 0
        self.lastI16 = 0
        
        log('Packet Decoder загружен')
        
        pass
        
    def bytesToU32(self, array, startIndex):
        if startIndex + 4 >= len(array):
            log('errorU32', startIndex, len(array))
            return self.lastU32
        
        u32 = 0
        # LSB first
        for i in range(4):
            u32 |= array[startIndex+i] << (i*8)
            

        self.lastU32 = u32

        return u32

    def bytesToI32(self, array, startIndex):
        if startIndex + 4 >= len(array):
            log('errorI32', startIndex, len(array))
            return self.lastI32

        i32 = 0
        # LSB first
        for i in range(4):
            i32 |= array[startIndex+i] << (i*8)

        # is bytes has sign
        if i32 & 0x8000:
            # inversion
            i32 = 0xFFFFFFFF - i32;
            # add +1
            i32 += 1
            # add sign
            i32 = -i32

        self.lastI32 = i32

        return i32

    def bytesToI16(self, array, startIndex):
        if startIndex + 2 >= len(array):
            log('errorI16', startIndex, len(array))
            return self.lastI16
        
        i16 = 0
        # LSB first
        for i in range(2):
            i16 |= array[startIndex+i] << (i*8)

        # is bytes has sign
        if i16 & 0x8000:
            # inversion
            i16 = 0xFFFF - i16;
            # add +1
            i16 += 1
            # add sign
            i16 = -i16
        
        self.lastI16 = i16
        return i16
        
    def decodeData(self, encodedBytes):
        log('из буффера ->', encodedBytes)

        offset = 0
        n = 0

        DECODING_START_NS = time.time_ns()
        decodedStr = ''
        n = 0
        offset = 0
        # LSB first in bytes
        
        # декодирование пакета
        # loop start tick
        if n == 0:
            decodedStr += str(self.bytesToU32(encodedBytes, offset) * 250)
            decodedStr += self.delimiter
            offset += 4
            n = 1
        # stlm temperature
        if n == 1:
            res = self.bytesToI16(encodedBytes, offset)
            res /= 256.0
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 2
        # ms5607 temperature
        if n == 2:
            res = self.bytesToU32(encodedBytes, offset)
            res /= 100.0
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 4
            n = 3
        # ms5607 altitude
        if n == 3:
            decodedStr += str(self.bytesToI32(encodedBytes, offset))
            decodedStr += self.delimiter
            offset += 4
            n = 4
        # bmp280 altitude
        if n == 4:
            decodedStr += str(self.bytesToI32(encodedBytes, offset))
            decodedStr += self.delimiter
            offset += 4
            n = 5
        # battery voltage
        if n == 5:
            R1 = 82000.0 # 82 kOm
            R2 = 200000.0 # 200 kOm
            res = self.bytesToU32(encodedBytes, offset)
            res = res * 3.3 / 4095.0
            res = res / (R2 / (R1+R2))
            res = round(res, 3)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 4
            n = 6
        # photoresistor value
        if n == 6:
            decodedStr += str(self.bytesToI16(encodedBytes, offset))
            decodedStr += self.delimiter
            offset += 2
            n = 7
        # gps lat
        if n == 7:
            lat1 = str(self.bytesToU32(encodedBytes, offset))
            offset += 4

            lat2 = str(self.bytesToU32(encodedBytes, offset))
            offset += 4

            latPart = lat1[:2]
            latPart2 = lat1[2:]
            lat = int(latPart) + float(str(latPart2 + '.' + lat2)) / 60.0
            lat = round(lat, 6)
            
            decodedStr += str(lat)
            decodedStr += self.delimiter

            n = 9
        # gps lon
        if n == 9:
            lon1 = str(self.bytesToU32(encodedBytes, offset))
            offset += 4

            lon2 = str(self.bytesToU32(encodedBytes, offset))
            offset += 4

            lonPart = lon1[:2]
            lonPart2 = lon1[2:]
            lon = int(lonPart) + float(str(lonPart2 + '.' + lon2)) / 60.0
            lon = round(lon, 6)
            
            decodedStr += str(lon)
            decodedStr += self.delimiter

            n = 11
        # lsm6 gyro x
        if n == 11:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 1000.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 12
        # lsm6 gyro y
        if n == 12:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 1000.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 13
        # lsm6 gyro z
        if n == 13:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 1000.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 14
        # lsm6 accelerometer x
        if n == 14:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 16.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 15
        # lsm6 accelerometer y
        if n == 15:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 16.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 16
        # lsm6 accelerometer z
        if n == 16:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 16.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 20
        # lsm303 compass x
        if n == 20:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 8.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 21
        # lsm303 compass y
        if n == 21:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 8.0
            res = round(res, 2)
            decodedStr += str(res)
            decodedStr += self.delimiter
            offset += 2
            n = 22
        # lsm303 compass z
        if n == 22:
            res = self.bytesToI16(encodedBytes, offset)
            res = res / 32768.0 * 8.0
            res = round(res, 2)
            decodedStr += str(res)
            offset += 2
            n = 23
        # packet end
        if n == 23:
            #if encodedBytes[offset] == ord('\n'):
                #log('конец пакета')
            n = -1
            
        DECODING_TIME_NS = time.time_ns() - DECODING_START_NS
        log('декодировано -> ', decodedStr, 'время[ms]:', ms(DECODING_TIME_NS))

        return decodedStr