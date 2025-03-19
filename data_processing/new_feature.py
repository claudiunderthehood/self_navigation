import pandas as pd

file_path = "robot_data.csv"
df = pd.read_csv(file_path, names=[
    "timestamp", "L_distance", "M_distance", "R_distance", 
    "light1", "light2", "line_sensors", "motor1", "motor2", "motor3", "motor4"
], skiprows=1)

df = df[~((df["motor1"] == 0) & (df["motor2"] == 0) & (df["motor3"] == 0) & (df["motor4"] == 0))]

def classify_movement(m1, m2, m3, m4):
    """Classify movement based on motor values."""
    if [m1, m2, m3, m4] == [0, 0, 0, 0]:
        return "STOP"
    elif [m1, m2, m3, m4] in [[800, 800, 800, 800], [600, 600, 600, 600]]:
        return "FORWARD"
    elif [m1, m2, m3, m4] == [-1200, -1200, -1200, -1200]:
        return "REVERSE"
    elif [m1, m2, m3, m4] == [-1600, -1600, 1600, 1600]:
        return "HARD_LEFT"
    elif [m1, m2, m3, m4] == [1600, 1600, -1600, -1600]:
        return "HARD_RIGHT"
    elif [m1, m2, m3, m4] == [1500, 1500, -800, -800]:
        return "SOFT_RIGHT"
    elif [m1, m2, m3, m4] in [[-800, -800, 1500, 1500], [-600, -600, 1500, 1500]]:
        return "SOFT_LEFT"
    elif [m1, m2, m3, m4] == [-2000, -2000, 2000, 2000]:
        return "REVERSE_LEFT"
    elif [m1, m2, m3, m4] == [2000, 2000, -2000, -2000]:
        return "REVERSE_RIGHT"
    elif [m1, m2, m3, m4] == [-1500, -1500, -1500, -1500]:
        return "ESCAPE_REVERSE"
    elif [m1, m2, m3, m4] == [-1800, -1800, 1800, 1800]:
        return "ESCAPE_LEFT"
    elif [m1, m2, m3, m4] == [1800, 1800, -1800, -1800]:
        return "ESCAPE_RIGHT"
    elif [m1, m2, m3, m4] == [2000, 2000, -1200, -1200]:
        return "AGGRESSIVE_RIGHT"
    elif [m1, m2, m3, m4] == [-1200, -1200, 2000, 2000]:
        return "AGGRESSIVE_LEFT"
    else:
        return "UNKNOWN"

df["direction"] = df.apply(lambda row: classify_movement(row["motor1"], row["motor2"], row["motor3"], row["motor4"]), axis=1)

updated_file_path = "robot_data_v2.csv"
df.to_csv(updated_file_path, index=False)

