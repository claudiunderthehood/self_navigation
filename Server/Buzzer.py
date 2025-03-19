import time
from gpiozero import Buzzer as GPIOBuzzer
from Command import COMMAND as cmd

class Buzzer:
    def __init__(self, pin=17):
        self.buzzer = GPIOBuzzer(pin)
    
    def run(self, command):
        self.buzzer.on() if command != "0" else self.buzzer.off()

if __name__ == '__main__':
    buzzer = Buzzer()
    buzzer.run('1')
    time.sleep(3)
    buzzer.run('0')
