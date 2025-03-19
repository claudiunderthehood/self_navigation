import time
from parameter import ParameterManager
from rpi_ledpixel import Freenove_RPI_WS281X
from spi_ledpixel import Freenove_SPI_LedPixel

class Led:
    def __init__(self):
        self.param = ParameterManager()
        self.pcb_version = self.param.get_pcb_version()
        self.pi_version = self.param.get_raspberry_pi_version()
        
        self.is_support_led_function = True
        if self.pcb_version == 1 and self.pi_version == 1:
            self.strip = Freenove_RPI_WS281X(8, 255, 'RGB')
        elif self.pcb_version == 2 and self.pi_version in [1, 2]:
            self.strip = Freenove_SPI_LedPixel(8, 255, 'GRB')
        else:
            print("PCB Version 1.0 is not supported on Raspberry PI 5.")
            self.is_support_led_function = False
    
    def color_wipe(self, change_color, wait_ms=50):
        if not self.is_support_led_function:
            return
        for i in range(self.strip.get_led_count()):
            self.strip.set_led_rgb_data(i, change_color)
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
    
    def wheel(self, pos):
        if not self.is_support_led_function or not (0 <= pos <= 255):
            return (0, 0, 0)
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)
    
    def rainbow(self, wait_ms=20, iterations=1):
        if not self.is_support_led_function:
            return
        for j in range(256 * iterations):
            for i in range(self.strip.get_led_count()):
                self.strip.set_led_rgb_data(i, self.wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
    
    def rainbow_cycle(self, wait_ms=20, iterations=5):
        if not self.is_support_led_function:
            return
        for j in range(256 * iterations):
            for i in range(self.strip.get_led_count()):
                self.strip.set_led_rgb_data(i, self.wheel((int(i * 256 / self.strip.get_led_count()) + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
    
    def theater_chase_rainbow(self, wait_ms=50):
        if not self.is_support_led_function:
            return
        led_count = self.strip.get_led_count()
        for j in range(0, 256, 5):
            for q in range(3):
                for i in range(0, led_count, 3):
                    self.strip.set_led_rgb_data((i + q) % led_count, self.wheel((i + j) % 255))
                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, led_count, 3):
                    self.strip.set_led_rgb_data((i + q) % led_count, [0, 0, 0])
    
    def led_index(self, index, r, g, b):
        if not self.is_support_led_function:
            return
        color = (r, g, b)
        for i in range(8):
            if index & 0x01:
                self.strip.set_led_rgb_data(i, color)
                self.strip.show()
            index >>= 1
    
    def led_mode(self, mode):
        while True:
            if mode == '1':
                self.color_wipe([255, 0, 0])
                self.color_wipe([0, 255, 0])
                self.color_wipe([0, 0, 255])
                self.color_wipe([0, 0, 0], 10)
            elif mode == '2':
                self.theater_chase_rainbow()
            elif mode == '3':
                self.rainbow()
            elif mode == '4':
                self.rainbow_cycle()
            else:
                self.color_wipe([0, 0, 0], 10)
                break

if __name__ == '__main__':
    print('Program is starting ...')
    led = LedController()
    try:
        print("Color wipe animation")
        led.color_wipe([255, 0, 0])
        led.color_wipe([0, 255, 0])
        led.color_wipe([0, 0, 255])
        print("Theater chase rainbow animation")
        led.theater_chase_rainbow()
        print("Rainbow animation")
        led.rainbow()
        print("Rainbow cycle animation")
        led.rainbow_cycle()
        led.color_wipe([0, 0, 0], 10)
    except KeyboardInterrupt:
        led.color_wipe([0, 0, 0], 10)
    finally:
        print("\nEnd of program")