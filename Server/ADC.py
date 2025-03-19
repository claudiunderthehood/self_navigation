import smbus
import time

class Adc:
    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.ADDRESS = 0x48
        self.PCF8591_CMD = 0x40
        self.ADS7830_CMD = 0x84
        
        for _ in range(3):
            aa = self.bus.read_byte_data(self.ADDRESS, 0xf4)
            self.Index = "PCF8591" if aa < 150 else "ADS7830"
            
    def analog_read_pcf8591(self, chn):
        values = [self.bus.read_byte_data(self.ADDRESS, self.PCF8591_CMD + chn) for _ in range(9)]
        return sorted(values)[4]
    
    def analog_write_pcf8591(self, value):
        self.bus.write_byte_data(self.ADDRESS, self.PCF8591_CMD, value)
        
    def recv_pcf8591(self, channel):
        while True:
            value1, value2 = self.analog_read_pcf8591(channel), self.analog_read_pcf8591(channel)
            if value1 == value2:
                break
        return round(value1 / 256.0 * 3.3, 2)
    
    def recv_ads7830(self, channel):
        command_set = self.ADS7830_CMD | ((((channel << 2) | (channel >> 1)) & 0x07) << 4)
        self.bus.write_byte(self.ADDRESS, command_set)
        while True:
            value1, value2 = self.bus.read_byte(self.ADDRESS), self.bus.read_byte(self.ADDRESS)
            if value1 == value2:
                break
        return round(value1 / 255.0 * 3.3, 2)
    
    def recv_adc(self, channel):
        return self.recv_pcf8591(channel) if self.Index == "PCF8591" else self.recv_ads7830(channel)
    
    def close(self):
        self.bus.close()

def loop():
    adc = Adc()
    try:
        while True:
            print(adc.recv_adc(0))
            print(adc.recv_adc(1))
            print(adc.recv_adc(2) * 3)
            time.sleep(1)
            print('----')
    except KeyboardInterrupt:
        adc.close()
        print("Program terminated.")

if __name__ == '__main__':
    print('Program is starting ...')
    loop()