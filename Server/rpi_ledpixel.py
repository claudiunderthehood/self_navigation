import time
from rpi_ws281x import Adafruit_NeoPixel, Color

class Freenove_RPI_WS281X:
    def __init__(self, led_count=4, bright=255, sequence="RGB"):
        self.set_led_type(sequence)
        self.set_led_count(led_count)
        self.set_led_brightness(bright)
        self.led_begin()
        self.set_all_led_color(0, 0, 0)

    def led_begin(self):
        self.strip = Adafruit_NeoPixel(self.get_led_count(), 18, 800000, 10, False, self.led_brightness, 0)
        self.led_init_state = 0 if self.strip.begin() else 1

    def check_rpi_ws281x_state(self):
        return self.led_init_state

    def led_close(self):
        self.set_all_led_rgb([0, 0, 0])

    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count

    def get_led_count(self):
        return self.led_count

    def set_led_type(self, rgb_type):
        led_type = ['RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR']
        led_type_offset = [0x06, 0x09, 0x12, 0x21, 0x18, 0x24]
        index = led_type.index(rgb_type) if rgb_type in led_type else -1
        offset = led_type_offset[index] if index != -1 else 0x06
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
        for i in range(self.get_led_count()):
            self.strip.setPixelColor(i, Color(*self.led_color[i * 3: i * 3 + 3]))
        self.strip.show()

if __name__ == '__main__':
    led = Freenove_RPI_WS281X(4, 255, "RGB")
    try:
        if led.check_rpi_ws281x_state() != 0:
            led.set_led_count(4)
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