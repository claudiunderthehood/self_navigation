import time
import random
import json
import numpy as np
import torch
from collections import deque

from Motor import Motor
from gpiozero import DistanceSensor
from servo import Servo
from PCA9685 import PCA9685

from direction_classifier_net import DirectionClassifierNet

MODEL_PATH = "best_model.pth"
CLASSES_JSON = "classes.json"

trigger_pin = 27
echo_pin    = 22
sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=3)

class Ultrasonic:
    def __init__(self):
        self.PWM = Motor()
        self.pwm_S = Servo()
        self.motor_values = [0, 0, 0, 0]

        self.pwm_S.setServoPwm('0', 90)
        time.sleep(0.5)

        self.last_L, self.last_M, self.last_R = 100, 100, 100
        self.prev_L, self.prev_M, self.prev_R = 100, 100, 100
        self.stuck_timer = None

        print("Loading classification model...")
        self.model = DirectionClassifierNet(
            input_dim=3,
            hidden_dim=64,
            output_dim=11,
            num_hidden_layers=2
        )
        self.model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        self.model.eval()
        print("Model loaded from:", MODEL_PATH)

        print("Loading classes list from JSON...")
        with open(CLASSES_JSON, "r") as f:
            self.classes_ = json.load(f)
        print("Classes found:", self.classes_)

        self.recent_preds = deque(maxlen=1)

        self.direction_to_motor = {
            "STOP":             [0, 0, 0, 0],
            "FORWARD":          [600, 600, 600, 600],
            "REVERSE":          [-1200, -1200, -1200, -1200],
            "HARD_LEFT":        [-1600, -1600, 1600, 1600],
            "HARD_RIGHT":       [1600, 1600, -1600, -1600],
            "SOFT_RIGHT":       [1500, 1500, -800, -800],
            "SOFT_LEFT":        [-800, -800, 1500, 1500],
            "REVERSE_LEFT":     [2000, 2000, -2000, -2000],
            "REVERSE_RIGHT":    [-2000, -2000, 2000, 2000],
            "ESCAPE_REVERSE":   [-1500, -1500, -1500, -1500],
            "ESCAPE_LEFT":      [-1800, -1800, 1800, 1800],
            "ESCAPE_RIGHT":     [1800, 1800, -1800, -1800],
            "AGGRESSIVE_RIGHT": [2000, 2000, -1200, -1200],
            "AGGRESSIVE_LEFT":  [-1200, -1200, 2000, 2000],
            "UNKNOWN":          [600, 600, 600, 600]
        }

    def get_distance(self):
        return int(sensor.distance * 100)

    def read_three_distances(self):
        distances = {}
        for angle, label in [(30, 'L'), (90, 'M'), (150, 'R')]:
            self.pwm_S.setServoPwm('0', angle)
            time.sleep(0.3)  # reduced delay for faster scanning
            d = self.get_distance()
            distances[label] = d
        return distances['L'], distances['M'], distances['R']

    def detect_stuck(self, L, M, R):
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
        print("🛑 Robot is stuck! Performing escape maneuver...")
        self.motor_values = [-1500, -1500, -1500, -1500]
        self.PWM.setMotorModel(*self.motor_values)
        time.sleep(1)

        if random.choice([True, False]):
            print("🔄 Turning LEFT to escape!")
            self.motor_values = [-1800, -1800, 1800, 1800]
        else:
            print("🔄 Turning RIGHT to escape!")
            self.motor_values = [1800, 1800, -1800, -1800]
        self.PWM.setMotorModel(*self.motor_values)
        time.sleep(1.0)

        self.motor_values = [600, 600, 600, 600]
        self.PWM.setMotorModel(*self.motor_values)

    def predict_direction_class(self, L, M, R):
        arr = np.array([[L, M, R]], dtype=np.float32)
        tensor_in = torch.from_numpy(arr)
        with torch.no_grad():
            logits = self.model(tensor_in)
            pred_idx = torch.argmax(logits, dim=1).item()
        return self.classes_[pred_idx]

    def majority_vote(self):
        if self.recent_preds:
            return self.recent_preds[-1]
        return "FORWARD"

    def run_once(self):
        L, M, R = self.read_three_distances()

        if self.detect_stuck(L, M, R):
            self.perform_unstuck_maneuver()
            return

        raw_direction = self.predict_direction_class(L, M, R)

        self.recent_preds.append(raw_direction)

        direction_str = self.majority_vote()
        print(f"Raw prediction: {raw_direction}, Final direction: {direction_str}")

        self.motor_values = self.direction_to_motor.get(direction_str, [600, 600, 600, 600])
        self.PWM.setMotorModel(*self.motor_values)
        print(f"Motor command set to: {self.motor_values}")

    def run(self):
        print("Starting rapid navigation. Press Ctrl+C to stop.")
        try:
            while True:
                self.run_once()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping. Setting motors to 0.")
            self.PWM.setMotorModel(0, 0, 0, 0)
            self.pwm_S.setServoPwm('0', 90)


if __name__ == "__main__":
    print("🚀 Robot Inference Script Starting with reduced sensor delay and immediate decision-making...")
    ultrasonic = Ultrasonic()
    ultrasonic.run()
