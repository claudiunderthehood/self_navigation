import pandas as pd

csv_file = "robot_data.csv"

df = pd.read_csv(csv_file)

condition_remove = (df["L_distance"] == 100) & (df["M_distance"] == 100) & (df["R_distance"] == 100) & \
                   (df["motor1"] == 0) & (df["motor2"] == 0) & (df["motor3"] == 0) & (df["motor4"] == 0)

df = df[~condition_remove]
condition_replace = (df["motor1"] == 800) & (df["motor2"] == 800) & (df["motor3"] == 800) & (df["motor4"] == 800)

df.loc[condition_replace, ["motor1", "motor2", "motor3", "motor4"]] = 600

df.to_csv(csv_file, index=False)