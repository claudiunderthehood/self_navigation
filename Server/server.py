import io
import os
import math
import socket
import  numpy as np
import struct
import time
import csv
import datetime
from picamera2 import Picamera2,Preview
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from picamera2.encoders import Quality
from threading import Condition
import fcntl
import  sys
import threading
from Motor import *
from servo import *
from Led import *
from Buzzer import *
from ADC import *
from Thread import *
from Light import *
from Ultrasonic import *
from Line_Tracking import *
from threading import Timer
from threading import Thread
from Command import COMMAND as cmd

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class Server:
    def __init__(self):
        self.PWM=Motor()
        self.servo=Servo()
        self.led=Led()
        self.ultrasonic=Ultrasonic()
        self.buzzer=Buzzer()
        self.adc=Adc()
        self.light=Light()
        self.infrared=Line_Tracking()
        self.tcp_Flag = True
        self.sonic=True
        self.Light=False
        self.Light=False
        self.Line=False
        self.Mode = 'one'
        self.endChar='\n'
        self.intervalChar='#'
        self.rotation_flag = False
        self.current_ultrasonic = 0.0
        self.current_light1 = 0
        self.current_light2 = 0
        self.current_line = '000'
        self.last_m1 = 0
        self.last_m2 = 0
        self.last_m3 = 0
        self.last_m4 = 0
        self.current_L = 0
        self.current_M = 0
        self.current_R = 0
        self.csv_file_path = "robot_data.csv"
        self.log_interval = 0.2
        self.keep_logging = True
        self.logger_thread = Thread(target=self.continuous_logger)
        self.logger_thread.start()
        self.ultrasonic_thread = Thread(target=self.continuous_ultrasonic_loop)
        self.ultrasonic_thread.start()
        self.init_csv_file()


    def init_csv_file(self):
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
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
                ])
            print("Created new CSV file with header.")
        else:
            print("CSV file already exists, will append data to it.")

    

    def log_data_to_csv(self, m1, m2, m3, m4):
        timestamp = datetime.datetime.now().isoformat()
        row = [
            timestamp,
            self.current_L,
            self.current_M,
            self.current_R,
            self.current_light1, 
            self.current_light2, 
            self.current_line, 
            m1, m2, m3, m4
        ]
        with open(self.csv_file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def continuous_logger(self):
        """
        Logs data every self.log_interval seconds.
        Even if the user is holding the same button (i.e. no new commands),
        the ultrasonic distance might be changing as we approach an obstacle.
        """
        while self.keep_logging:
            m1 = self.last_m1
            m2 = self.last_m2
            m3 = self.last_m3
            m4 = self.last_m4

            self.log_data_to_csv(m1, m2, m3, m4)

            time.sleep(self.log_interval)
    
    def continuous_ultrasonic_loop(self):
        while self.sonic:
            L, M, R = self.ultrasonic.get_last_sensor_values()
            motor_values = self.ultrasonic.get_motor_values()
            
            self.current_L, self.current_M, self.current_R = L, M, R
            self.last_m1, self.last_m2, self.last_m3, self.last_m4 = motor_values
            
            time.sleep(0.2)


    def get_interface_ip(self, ifname="wlan0"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])

    def StartTcpServer(self):
        HOST = '0.0.0.0'

        self.server_socket1 = socket.socket()
        self.server_socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_socket1.bind((HOST, 5000))
        self.server_socket1.listen(1)

        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_socket.bind((HOST, 8000))
        self.server_socket.listen(1)

        print("Server listening on 0.0.0.0 (ports 5000 & 8000).")
        print("Clients can connect via any IP assigned to the Pi:")
        try:
            ip_wlan0 = self.get_interface_ip("wlan0")
            ip_wlan1 = self.get_interface_ip("wlan1")
            print(f"  wlan0: {ip_wlan0}\n  wlan1: {ip_wlan1}")
        except Exception as e:
            print(f'Error on Starting TCP Server: {e}')
            pass

    def StopTcpServer(self):
        self.keep_logging = False

        try:
            self.connection.close()
            self.connection1.close()
        except Exception as e:
            print ('\n'+"No client connection")

    def Reset(self):
        self.StopTcpServer()
        self.StartTcpServer()
        self.SendVideo=Thread(target=self.sendvideo)
        self.ReadData=Thread(target=self.readdata)
        self.SendVideo.start()
        self.ReadData.start()
    def send(self,data):
        self.connection1.send(data.encode('utf-8'))
    def sendvideo(self):
        try:
            self.connection,self.client_address = self.server_socket.accept()
            self.connection=self.connection.makefile('wb')
        except:
            pass
        self.server_socket.close()
        print ("socket video connected ... ")
        camera = Picamera2()
        camera.configure(camera.create_video_configuration(main={"size": (400, 300)}))
        output = StreamingOutput()
        encoder = JpegEncoder(q=90)
        camera.start_recording(encoder, FileOutput(output),quality=Quality.VERY_HIGH)
        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            try:
                lenFrame = len(output.frame)
                lengthBin = struct.pack('<I', lenFrame)
                self.connection.write(lengthBin)
                self.connection.write(frame)
            except Exception as e:
                camera.stop_recording()
                camera.close()
                print ("End transmit ... " )
                break

    def stopMode(self):
        try:
            stop_thread(self.infraredRun)
            self.PWM.setMotorModel(0,0,0,0)
        except:
            pass
        finally:
            self.PWM.setMotorModel(0,0,0,0)
        try:
            stop_thread(self.lightRun)
        except:
            pass
        finally:
            self.PWM.setMotorModel(0,0,0,0)
        try:
            stop_thread(self.ultrasonicRun)
        except:
            pass
        finally:
            self.PWM.setMotorModel(0,0,0,0)
            self.servo.setServoPwm('0',90)
            self.servo.setServoPwm('1',90)
        self.sonic=False
        self.Light=False
        self.Line=False         
        self.send('CMD_MODE'+'#1'+'#'+'0'+'#'+'0'+'\n')
        self.send('CMD_MODE'+'#3'+'#'+'0'+'\n')
        self.send('CMD_MODE'+'#2'+'#'+'000'+'\n')           
    def readdata(self):
        try:
            try:
                self.connection1,self.client_address1 = self.server_socket1.accept()
                print ("Client connection successful !")
            except:
                print ("Client connect failed")
            restCmd=""
            self.server_socket1.close()
            while True:
                try:
                    AllData=restCmd+self.connection1.recv(1024).decode('utf-8')
                except:
                    if self.tcp_Flag:
                        self.Reset()
                    break
                print(AllData)
                if len(AllData) < 5:
                    restCmd=AllData
                    if restCmd=='' and self.tcp_Flag:
                        self.Reset()
                        break
                restCmd=""
                if AllData=='':
                    break
                else:
                    cmdArray=AllData.split("\n")
                    if(cmdArray[-1] != ""):
                        restCmd=cmdArray[-1]
                        cmdArray=cmdArray[:-1]

                for oneCmd in cmdArray:
                    data=oneCmd.split("#")
                    if data==None:
                        continue
                    elif cmd.CMD_MODE in data:
                        if data[1]=='one' or data[1]=="1":
                            self.stopMode()
                            self.Mode='one'
                        elif data[1]=='two' or data[1]=="3":
                            self.stopMode()
                            self.Mode='two'
                            self.lightRun=Thread(target=self.light.run)
                            self.lightRun.start()
                            self.Light = True
                            self.lightTimer = threading.Timer(0.3, self.sendLight)
                            self.lightTimer.start()
                        elif data[1]=='three' or data[1]=="4":
                            self.stopMode()
                            self.Mode='three'
                            self.ultrasonicRun=threading.Thread(target=self.ultrasonic.run)
                            self.ultrasonicRun.start()
                            self.sonic=True
                            self.ultrasonicTimer = threading.Timer(0.2,self.sendUltrasonic)
                            self.ultrasonicTimer.start()
                        elif data[1]=='four' or data[1]=="2":
                            self.stopMode()
                            self.Mode='four'
                            self.infraredRun=threading.Thread(target=self.infrared.run)
                            self.infraredRun.start()
                            self.Line=True
                            self.lineTimer = threading.Timer(0.4,self.sendLine)
                            self.lineTimer.start()

                    elif (cmd.CMD_MOTOR in data) and self.Mode=='one':
                        try:
                            data1=int(data[1])
                            data2=int(data[2])
                            data3=int(data[3])
                            data4=int(data[4])
                            if data1==None or data2==None or data2==None or data3==None:
                                continue
                            self.PWM.setMotorModel(data1,data2,data3,data4)
                            
                            self.last_m1 = data1
                            self.last_m2 = data2
                            self.last_m3 = data3
                            self.last_m4 = data4
                        except Exception as e:
                            print("CMD_MOTOR exception: ", e)
                            pass
                    elif (cmd.CMD_M_MOTOR in data) and self.Mode=='one':
                        try:
                            data1=int(data[1])
                            data2=int(data[2])
                            data3=int(data[3])
                            data4=int(data[4])

                            LX = -int((data2 * math.sin(math.radians(data1))))
                            LY = int(data2 * math.cos(math.radians(data1)))
                            RX = int(data4 * math.sin(math.radians(data3)))
                            RY = int(data4 * math.cos(math.radians(data3)))

                            FR = LY - LX + RX
                            FL = LY + LX - RX
                            BL = LY - LX - RX
                            BR = LY + LX + RX

                            if data1==None or data2==None or data2==None or data3==None:
                                continue
                            self.PWM.setMotorModel(FL,BL,FR,BR)
                            self.log_data_to_csv(FL, BL, FR, BR)
                        except:
                            pass
                    elif (cmd.CMD_CAR_ROTATE in data) and self.Mode == 'one':
                        try:

                            data1 = int(data[1])
                            data2 = int(data[2])
                            data3 = int(data[3])
                            data4 = int(data[4])
                            set_angle = data3
                            if data4 == 0:
                                try:
                                    stop_thread(Rotate_Mode)
                                    self.rotation_flag = False
                                except:
                                    pass
                                LX = -int((data2 * math.sin(math.radians(data1))))
                                LY = int(data2 * math.cos(math.radians(data1)))
                                RX = int(data4 * math.sin(math.radians(data3)))
                                RY = int(data4 * math.cos(math.radians(data3)))

                                FR = LY - LX + RX
                                FL = LY + LX - RX
                                BL = LY - LX - RX
                                BR = LY + LX + RX

                                if data1 == None or data2 == None or data2 == None or data3 == None:
                                    continue
                                self.PWM.setMotorModel(FL, BL, FR, BR)
                                self.log_data_to_csv(FL, BL, FR, BR)
                            elif self.rotation_flag == False:
                                self.angle = data[3]
                                try:
                                    stop_thread(Rotate_Mode)
                                except:
                                    pass
                                self.rotation_flag = True
                                Rotate_Mode = Thread(target=self.PWM.Rotate, args=(data3,))
                                Rotate_Mode.start()
                        except:
                            pass
                    elif cmd.CMD_SERVO in data:
                        try:
                            data1 = data[1]
                            data2 = int(data[2])
                            if data1 == None or data2 == None:
                                continue
                            self.servo.setServoPwm(data1,data2)
                        except:
                            pass

                    elif cmd.CMD_LED in data:
                        try:
                            data1=int(data[1])
                            data2=int(data[2])
                            data3=int(data[3])
                            data4=int(data[4])
                            if data1==None or data2==None or data3==None or data4==None:
                                continue
                            self.led.ledIndex(data1,data2,data3,data4)
                        except:
                            pass
                    elif cmd.CMD_LED_MOD in data:
                        self.LedMoD=data[1]
                        try:
                            stop_thread(self.Led_Run_Mode)
                        except:
                            pass
                        time.sleep(0.1)
                        self.Led_Run_Mode=Thread(target=self.led.ledMode,args=(data[1],))
                        self.Led_Run_Mode.start()
                    elif cmd.CMD_SONIC in data:
                        if data[1]=='1':
                            self.sonic=True
                            self.ultrasonicTimer = threading.Timer(0.5,self.sendUltrasonic)
                            self.ultrasonicTimer.start()
                        else:
                            self.sonic=False
                    elif cmd.CMD_BUZZER in data:
                        try:
                            self.buzzer.run(data[1])
                        except:
                            pass
                    elif cmd.CMD_LIGHT in data:
                        if data[1]=='1':
                            self.Light=True
                            self.lightTimer = threading.Timer(0.3,self.sendLight)
                            self.lightTimer.start()
                        else:
                            self.Light=False
                    elif cmd.CMD_POWER in data:
                        ADC_Power=self.adc.recvADC(2)*3
                        try:
                            self.send(cmd.CMD_POWER+'#'+str(round(ADC_Power, 2))+'\n')
                        except:
                            pass
        except Exception as e:
            print(e)
        self.StopTcpServer()

    def sendUltrasonic(self):
        if self.sonic==True:
            ADC_Ultrasonic=self.ultrasonic.get_distance()
            self.current_ultrasonic = ADC_Ultrasonic

            try:
                self.send(cmd.CMD_MODE+"#"+"3"+"#"+str(ADC_Ultrasonic)+'\n')
            except:
                self.sonic=False
                
            self.ultrasonicTimer = threading.Timer(0.23,self.sendUltrasonic)
            self.ultrasonicTimer.start()

    def sendLight(self):
        if self.Light==True:
            ADC_Light1=self.adc.recvADC(0)
            ADC_Light2=self.adc.recvADC(1)

            self.current_light1 = ADC_Light1
            self.current_light2 = ADC_Light2
            
            try:
                self.send("CMD_MODE#1"+'#'+str(ADC_Light1)+'#'+str(ADC_Light2)+'\n')
            except:
                self.Light=False
            self.lightTimer = threading.Timer(0.17,self.sendLight)
            self.lightTimer.start()

    def sendLine(self):
        if self.Line==True:
            Line1= IR01_sensor.value
            Line2= IR02_sensor.value
            Line3= IR03_sensor.value
            self.current_line = f"{Line1}{Line2}{Line3}"

            try:
                self.send("CMD_MODE#2"+'#'+str(Line1)+str(Line2)+str(Line3)+'\n')
            except:
                self.Line=False
            self.LineTimer = threading.Timer(0.20,self.sendLine)
            self.LineTimer.start()
    def Power(self):
        while True:
            ADC_Power=self.adc.recvADC(2)*3
            try:
                self.send(cmd.CMD_POWER+'#'+str(round(ADC_Power, 2))+'\n')
            except:
                pass
            time.sleep(3)
            if ADC_Power < 6.5:
                for i in range(4):
                    self.buzzer.run('1')
                    time.sleep(0.1)
                    self.buzzer.run('0')
                    time.sleep(0.1)
            elif ADC_Power< 7:
                for i in range(2):
                    self.buzzer.run('1')
                    time.sleep(0.1)
                    self.buzzer.run('0')
                    time.sleep(0.1)
            else:
                self.buzzer.run('0')
if __name__=='__main__':
    pass

