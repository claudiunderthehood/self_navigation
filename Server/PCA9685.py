import os
import json
import subprocess
import time
import math
import smbus

class ParameterManager:
    PARAM_FILE = 'params.json'
    
    def __init__(self):
        self.file_path = self.PARAM_FILE
        if not self.file_exists() or not self.validate_params():
            self.deal_with_param()
    
    def file_exists(self, file_path=None):
        return os.path.exists(file_path or self.file_path)
    
    def validate_params(self, file_path=None):
        file_path = file_path or self.file_path
        if not self.file_exists(file_path):
            return False
        try:
            with open(file_path, 'r') as file:
                params = json.load(file)
                return params.get('Pcb_Version') in [1, 2] and params.get('Pi_Version') in [1, 2]
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading file: {e}")
            return False
    
    def get_param(self, param_name, file_path=None):
        file_path = file_path or self.file_path
        if self.validate_params(file_path):
            with open(file_path, 'r') as file:
                return json.load(file).get(param_name)
        return None
    
    def set_param(self, param_name, value, file_path=None):
        file_path = file_path or self.file_path
        params = {}
        if self.file_exists(file_path):
            with open(file_path, 'r') as file:
                params = json.load(file)
        params[param_name] = value
        with open(file_path, 'w') as file:
            json.dump(params, file, indent=4)
    
    def delete_param_file(self, file_path=None):
        file_path = file_path or self.file_path
        if self.file_exists(file_path):
            os.remove(file_path)
            print(f"Deleted {file_path}")
    
    def create_param_file(self, file_path=None):
        file_path = file_path or self.file_path
        with open(file_path, 'w') as file:
            json.dump({'Pcb_Version': 2, 'Pi_Version': self.get_raspberry_pi_version()}, file, indent=4)
    
    def get_raspberry_pi_version(self):
        try:
            result = subprocess.run(['cat', '/sys/firmware/devicetree/base/model'], capture_output=True, text=True)
            return 2 if "Raspberry Pi 5" in result.stdout.strip() else 1
        except Exception as e:
            print(f"Error getting Raspberry Pi version: {e}")
            return 1
    
    def deal_with_param(self):
        if not self.file_exists() or not self.validate_params():
            print(f"Parameter file {self.PARAM_FILE} does not exist or contains invalid parameters.")
            user_input_required = True
        else:
            user_input_required = input("Do you want to re-enter the hardware versions? (yes/no): ").strip().lower() == 'yes'
        
        if user_input_required:
            while True:
                try:
                    pcb_version = int(input("Enter PCB Version (1 or 2): "))
                    if pcb_version in [1, 2]:
                        break
                    print("Invalid PCB Version. Please enter 1 or 2.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            pi_version = self.get_raspberry_pi_version()
            self.create_param_file()
            self.set_param('Pcb_Version', pcb_version)
            self.set_param('Pi_Version', pi_version)
        else:
            print("Skipping modification of hardware version.")
    
    def get_pcb_version(self):
        return self.get_param('Pcb_Version')
    
    def get_pi_version(self):
        return self.get_param('Pi_Version')

class PCA9685:
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06
    __LED0_OFF_L = 0x08
    
    def __init__(self, address=0x40, debug=False):
        self.bus = smbus.SMBus(1)
        self.address = address
        self.debug = debug
        self.write(self.__MODE1, 0x00)
    
    def write(self, reg, value):
        self.bus.write_byte_data(self.address, reg, value)
    
    def read(self, reg):
        return self.bus.read_byte_data(self.address, reg)
    
    def setPWMFreq(self, freq):
        prescaleval = 25000000.0 / 4096.0 / float(freq) - 1.0
        prescale = int(math.floor(prescaleval + 0.5))
        oldmode = self.read(self.__MODE1)
        self.write(self.__MODE1, (oldmode & 0x7F) | 0x10)
        self.write(self.__PRESCALE, prescale)
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)
    
    def setPWM(self, channel, on, off):
        self.write(self.__LED0_ON_L + 4 * channel, on & 0xFF)
        self.write(self.__LED0_ON_L + 4 * channel + 1, on >> 8)
        self.write(self.__LED0_OFF_L + 4 * channel, off & 0xFF)
        self.write(self.__LED0_OFF_L + 4 * channel + 1, off >> 8)
    
    def setMotorPwm(self, channel, duty):
        self.setPWM(channel, 0, duty)
    
    def setServoPulse(self, channel, pulse):
        self.setPWM(channel, 0, int(pulse * 4096 / 20000))

if __name__ == '__main__':
    manager = ParameterManager()
    manager.deal_with_param()
    if manager.file_exists("params.json") and manager.validate_params("params.json"):
        print(f"PCB Version: {manager.get_pcb_version()}.0")
        print(f"Raspberry PI version is {'less than 5' if manager.get_raspberry_pi_version() == 1 else '5' }.")