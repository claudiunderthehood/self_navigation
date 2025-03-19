import spidev
import numpy

class Freenove_SPI_LedPixel:
    def __init__(self, count=8, bright=255, sequence='GRB', bus=0, device=0):
        self.set_led_type(sequence)
        self.set_led_count(count)
        self.set_led_brightness(bright)
        self.led_begin(bus, device)
        self.set_all_led_color(0, 0, 0)
       
    def led_begin(self, bus=0, device=0):
        self.bus, self.device = bus, device
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("Check /boot/firmware/config.txt for SPI configuration.")
            self.led_init_state = 0
    
    def check_spi_state(self):
        return self.led_init_state
    
    def led_close(self):
        self.set_all_led_rgb([0, 0, 0])
        self.spi.close()
    
    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count
    
    def get_led_count(self):
        return self.led_count
    
    def set_led_type(self, rgb_type):
        led_types = ['RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR']
        offsets = [0x06, 0x09, 0x12, 0x21, 0x18, 0x24]
        index = led_types.index(rgb_type) if rgb_type in led_types else -1
        offset = offsets[index] if index != -1 else 0x06
        self.led_red_offset, self.led_green_offset, self.led_blue_offset = (offset >> 4) & 0x03, (offset >> 2) & 0x03, offset & 0x03
    
    def set_led_brightness(self, brightness):
        self.led_brightness = brightness
        for i in range(self.get_led_count()):
            self.set_led_rgb_data(i, self.led_original_color)
    
    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, *color)
    
    def set_ledpixel(self, index, r, g, b):
        p = [0, 0, 0]
        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)
        for i in range(3):
            self.led_color[index * 3 + i] = p[i]
    
    def set_all_led_rgb(self, color):
        for i in range(self.get_led_count()):
            self.set_led_rgb_data(i, color)
        self.show()
    
    def show(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)
        for ibit in range(8):
            tx[7 - ibit::8] = ((d >> ibit) & 1) * 0x78 + 0x80  
        if self.led_init_state:
            self.spi.xfer(tx.tolist(), int(8 / 1.25e-6) if self.bus == 0 else int(8 / 1.0e-6))
    
if __name__ == '__main__':
    import time
    import os
    print("spidev version:", spidev.__version__)
    os.system("ls /dev/spi*")
    
    led = Freenove_SPI_LedPixel(8, 255)
    try:
        if led.check_spi_state():
            led.set_all_led_rgb([255, 0, 0])
            time.sleep(0.5)
            led.set_all_led_rgb([0, 255, 0])
            time.sleep(0.5)
            led.set_all_led_rgb([0, 0, 255])
            time.sleep(0.5)
            led.set_all_led_rgb([255, 255, 255])
            time.sleep(0.5)
            led.set_all_led_rgb([0, 0, 0])
            time.sleep(0.5)
            led.set_led_brightness(20)
            while True:
                for j in range(255):
                    for i in range(led.led_count):
                        led.set_led_rgb_data(i, [255 - j, j, 0])
                    led.show()
                    time.sleep(0.002)
        else:
            led.led_close()
    except KeyboardInterrupt:
        led.led_close()