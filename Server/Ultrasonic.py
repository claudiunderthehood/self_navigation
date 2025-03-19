import time
import random
from Motor import *
from gpiozero import DistanceSensor
from servo import *
from PCA9685 import PCA9685

trigger_pin = 27
echo_pin = 22
sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=3)

class Ultrasonic:
    def __init__(self):
        self.PWM = Motor()
        self.pwm_S = Servo()
        self.motor_values = [0, 0, 0, 0]  

        self.last_L, self.last_M, self.last_R = 100, 100, 100

        self.prev_L, self.prev_M, self.prev_R = 100, 100, 100
        self.stuck_timer = None  

        self.pwm_S.setServoPwm('0', 90)
        time.sleep(0.5)

    def get_distance(self):
        """Gets the current distance from the ultrasonic sensor in cm."""
        return int(sensor.distance * 100)

    def detect_stuck(self, L, M, R):
        """
        Detect if the bot is stuck:
        - If moving forward (800, 800, 800, 800) but L, M, R **stay the same for 1.5 sec**, it's stuck.
        """
        moving_forward = self.motor_values == [600, 600, 600, 600]

        if moving_forward:
            if (L == self.prev_L and M == self.prev_M and R == self.prev_R):
                if self.stuck_timer is None:
                    self.stuck_timer = time.time()

                if time.time() - self.stuck_timer > 1.5:
                    return True
            else:
                self.stuck_timer = None

        self.prev_L, self.prev_M, self.prev_R = L, M, R
        return False

    def perform_unstuck_maneuver(self):
        """Executes an escape maneuver when the robot is stuck."""
        print("🛑 Robot is stuck! Performing escape maneuver...")

        self.motor_values = [-1500, -1500, -1500, -1500]
        self.PWM.setMotorModel(-1500, -1500, -1500, -1500)
        time.sleep(1)

        if random.choice([True, False]):
            print("🔄 Turning LEFT to escape!")
            self.motor_values = [-1800, -1800, 1800, 1800]  
            self.PWM.setMotorModel(-1800, -1800, 1800, 1800)
        else:
            print("🔄 Turning RIGHT to escape!")
            self.motor_values = [1800, 1800, -1800, -1800]  
            self.PWM.setMotorModel(1800, 1800, -1800, -1800)

        time.sleep(0.7)

        self.motor_values = [600, 600, 600, 600]
        self.PWM.setMotorModel(600, 600, 600, 600)

    def run_motor(self, L, M, R):
        """Controls movement based on sensor readings."""
        self.last_L, self.last_M, self.last_R = L, M, R

        if self.detect_stuck(L, M, R):
            self.perform_unstuck_maneuver()
            return  

        if (L < 30 and M < 30 and R < 30) or M < 30:
            self.motor_values = [-1200, -1200, -1200, -1200]
            self.PWM.setMotorModel(-1200, -1200, -1200, -1200)  
            time.sleep(0.2)

            if L < R:
                self.motor_values = [1600, 1600, -1600, -1600]
                self.PWM.setMotorModel(1600, 1600, -1600, -1600)
            else:
                self.motor_values = [-1600, -1600, 1600, 1600]
                self.PWM.setMotorModel(-1600, -1600, 1600, 1600)
            time.sleep(0.3)

        elif L < 30 and M < 30:
            self.motor_values = [2000, 2000, -2000, -2000]
            self.PWM.setMotorModel(2000, 2000, -2000, -2000)
            time.sleep(0.3)

        elif R < 30 and M < 30:
            self.motor_values = [-2000, -2000, 2000, 2000]
            self.PWM.setMotorModel(-2000, -2000, 2000, 2000)
            time.sleep(0.3)

        elif L < 20:
            self.motor_values = [1500, 1500, -800, -800]
            self.PWM.setMotorModel(1500, 1500, -800, -800)
            if L < 10:
                self.motor_values = [2000, 2000, -1200, -1200]
                self.PWM.setMotorModel(2000, 2000, -1200, -1200)
            time.sleep(0.3)

        elif R < 20:
            self.motor_values = [-600, -600, 1500, 1500]
            self.PWM.setMotorModel(-800, -800, 1500, 1500)
            if R < 10:
                self.motor_values = [-1200, -1200, 2000, 2000]
                self.PWM.setMotorModel(-1200, -1200, 2000, 2000)
            time.sleep(0.3)

        else:
            self.motor_values = [600, 600, 600, 600]
            self.PWM.setMotorModel(600, 600, 600, 600)

    def run(self):
        """Main loop for ultrasonic navigation."""
        self.PWM = Motor()
        self.pwm_S = Servo()

        for i in range(30, 151, 60):
            self.pwm_S.setServoPwm('0', i)
            time.sleep(0.2)
            if i == 30:
                L = self.get_distance()
            elif i == 90:
                M = self.get_distance()
            else:
                R = self.get_distance()
                
        while True:
            for i in range(90, 30, -60):
                self.pwm_S.setServoPwm('0', i)
                time.sleep(0.2)
                if i == 30:
                    L = self.get_distance()
                elif i == 90:
                    M = self.get_distance()
                else:
                    R = self.get_distance()
                self.run_motor(L, M, R)

            for i in range(30, 151, 60):
                self.pwm_S.setServoPwm('0', i)
                time.sleep(0.2)
                if i == 30:
                    L = self.get_distance()
                elif i == 90:
                    M = self.get_distance()
                else:
                    R = self.get_distance()
                self.run_motor(L, M, R)

    def get_motor_values(self):
        return self.motor_values

    def get_last_sensor_values(self):
        return self.last_L, self.last_M, self.last_R

ultrasonic = Ultrasonic()

if __name__ == '__main__':
    print('🚀 Robot is starting...')
    try:
        ultrasonic.run()
    except KeyboardInterrupt:
        PWM.setMotorModel(0, 0, 0, 0)
        ultrasonic.pwm_S.setServoPwm('0', 90)