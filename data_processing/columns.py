import pandas as pd

csv_file = "robot_data.csv"
column_names = [
    "timestamp",
    "L_distance",
    "M_distance",  
    "R_distance",  
    "light1",
    "light2",
    "line_sensors",
    "motor1",
    "motor2",
    "motor3",
    "motor4"
]

df = pd.read_csv(csv_file, header=None)  
df.columns = column_names
df.to_csv(csv_file, index=False)